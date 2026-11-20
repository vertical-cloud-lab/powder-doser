"""Shared numbers for the gear-mesh preload analysis (both carousel designs).

Everything is in Sam's studio frame (cad/paternoster/params.py): the module's hinge
axis is y through the origin, the auger runs along +x from its outlet (x = 0.4 mm),
z is up from the plate (plate underside z = -18). The module is the same in both
designs (Sam's Oct 13 mounting plate + the lab auger + cap), and so is the station
drive (Sam's electronics carriage with the doser's NEMA 11 and a 20T pinion under the
auger's 44T gear). Only what holds the hinge differs: a gondola hanging from the chain
(paternoster) or a carriage bolted to the chain (v2).

Sources:
  out/gear_geometry.json  measured from the auger STEP (measure_gear.py)
  out/mass_props.json     CAD volumes x PETG density x solid fraction (mass_props.py)
  hardware/vendor-files/stepperonline-11hs18-0674s/SPECS.md (motor)
  Sam's carriage STEP: NEMA 11 pilot axis at z = -33.0 with the carriage top at -18.9
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)

G = 9.81

# ---------------------------------------------------------------- gears
_GG = json.loads((OUT / "gear_geometry.json").read_text())
M = _GG["module_mm"]                    # 1.0
PHI = math.radians(20.0)                # fit 19.97 deg
Z1, Z2 = 20, _GG["teeth"]               # NEMA 11 pinion, auger gear
R1, R2 = M * Z1 / 2, M * Z2 / 2         # pitch radii 10, 22
RB1, RB2 = R1 * math.cos(PHI), R2 * math.cos(PHI)
RA1, RA2 = R1 + M, _GG["tip_radius_mm"]                 # 11.0, 23.0
RF1, RF2 = R1 - (R2 - _GG["root_radius_mm"]), _GG["root_radius_mm"]   # same dedendum as the measured gear (1.157 m)
FACE = _GG["face_width_mm"]             # 10 mm (the pinion assumed 10 mm too)
A0 = R1 + R2                            # 32.0 mm standard centre distance
GEAR_X = 0.4 + sum(_GG["face_z_mm"]) / 2  # 83.73 mm: gear mid-plane from the hinge (Sam's x)
PB = math.pi * M * math.cos(PHI)        # base pitch 2.952 mm

# Sam's carriage sets the centre distance by face contact: its top (z -18.9 as drawn) meets the
# plate underside (z -18.0); the NEMA 11 pilot is 33.0 below the auger axis as drawn, so 32.1 docked.
A_DOCK = 33.0 - (18.9 - 18.0)           # 32.1 mm

# ---------------------------------------------------------------- motor (StepperOnline 11HS18-0674S)
T_HOLD = 0.10                           # N*m at the rated 0.67 A, both phases on
I_RATED = 0.67
R_PH, L_PH = 6.8, 4.9e-3                # ohm, H
N_ROTOR = 50                            # rotor teeth (1.8 deg full step)
J_ROTOR = 9.0e-7                        # kg*m^2: 9 g*cm^2, typical for a 45 mm NEMA 11 (assumed)
M_MOTOR = 0.180                         # kg (SPECS.md)

# ---------------------------------------------------------------- module (from the CAD)
_MP = json.loads((OUT / "mass_props.json").read_text())
M_MOD = _MP["module_empty"]["mass_g"] / 1000          # 0.101 kg
X_COM, Z_COM = _MP["module_empty"]["com_mm"][0], _MP["module_empty"]["com_mm"][2]   # 96.0, -3.2 mm
I_HINGE = _MP["module_empty"]["Iy_hinge_gmm2"] * 1e-9     # kg*m^2 about the hinge
M_AUG = _MP["auger_rotating"]["mass_g"] / 1000
J_AUG = _MP["auger_rotating"]["Ix_axis_gmm2"] * 1e-9      # kg*m^2 about the auger axis
M_CARR = 0.25                           # Sam's electronics carriage with the NEMA 11 and the solenoid

# Powder fills. The tube holds 79 mL (sim/AUGER-SIM.md). x_p: centroid from the hinge, mm.
# Horizontal, a partial fill lies along the whole bore (flight section 12-83 mm, storage 83-250 mm);
# tilted cap-end up it slides down onto the flights, so the tilted cases use a lower centroid.
POWDER_ROLL_X = 150.0                   # level module
POWDER_TILT_X = 110.0                   # tilted 15 deg or more (powder slid toward the flights)
FILLS = {"empty": 0.0, "20 g": 0.020, "60 g": 0.060, "150 g (dense metal)": 0.150}

# Dock: the carriage's top rim meets the plate underside over x = 25-73 mm (Sam's STEP).
DOCK_X = (25.0, 73.3)

# ---------------------------------------------------------------- materials
MAT = {
    # E (MPa), nu, allowable bending (MPa, 1e7 cycles, one-way), allowable contact (MPa), mu on PETG
    "PETG (printed)": dict(E=2000.0, nu=0.38, Sb=12.0, Sc=30.0),
    "PLA (printed)": dict(E=3000.0, nu=0.36, Sb=10.0, Sc=30.0),
    "steel": dict(E=200000.0, nu=0.30, Sb=200.0, Sc=600.0),
    "brass": dict(E=100000.0, nu=0.34, Sb=60.0, Sc=300.0),
}
MU = {"PETG on PETG, dry": 0.30, "steel on PETG, dry": 0.20, "steel on PETG, PTFE dry lube": 0.10}


def weight_moment(m_powder: float, world_tilt_deg: float, x_powder: float | None = None) -> float:
    """Gravity moment (N*mm) that holds the plate down on the carriage at a world tilt (cap end up)."""
    a = math.radians(world_tilt_deg)
    if x_powder is not None:
        xp = x_powder
    else:   # the powder slides toward the flights as the cap end rises (all of it by 15 deg)
        xp = POWDER_ROLL_X + (POWDER_TILT_X - POWDER_ROLL_X) * min(1.0, max(world_tilt_deg, 0.0) / 15.0)
    m_mod = M_MOD * G * (X_COM * math.cos(a) - Z_COM * math.sin(a))
    m_pow = m_powder * G * xp * math.cos(a)
    return m_mod + m_pow


def separating_ratio(mu: float, phi_op: float = PHI) -> float:
    """Worst-case radial (separating) force per unit tangential force over a mesh cycle: tan(phi) + mu."""
    return math.tan(phi_op) + mu


def operating_pressure_angle(a: float) -> float:
    return math.acos(A0 * math.cos(PHI) / a)


def contact_ratio(a: float) -> float:
    pa = operating_pressure_angle(a)
    L = math.sqrt(max(RA1 ** 2 - RB1 ** 2, 0)) + math.sqrt(max(RA2 ** 2 - RB2 ** 2, 0)) - a * math.sin(pa)
    return L / PB
