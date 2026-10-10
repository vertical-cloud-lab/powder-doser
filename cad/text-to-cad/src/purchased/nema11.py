"""NEMA 11 stepper motor, OMC StepperOnline 11HS18-0674S, from the vendor STEP.

Input
    The manufacturer's STEP, tracked in this repository with its provenance
    (hardware/vendor-files/stepperonline-11hs18-0674s/: SOURCES.txt, SPECS.md).
    It is read IN PLACE, by a path anchored on this file, rather than copied
    into STEP/imported/, so the repository keeps a single copy of the 1.2 MB
    vendor file next to its datasheets.  (step.parts has no 11HS18-0674S, only
    generic "analytic simplified" NEMA 11 bodies of 20/28/34/40/48/60 mm; see
    checks/results/purchased_step_parts.json.)

Frame: that of PR #170's components/purchased/nema11-11hs18-0674s.step
    mounting face on z = 0, body in -z, Ø22 x 2 pilot and Ø5 x 20 D-cut shaft
    on +z through the origin, the D-flat facing +y (y = +2), 4 x M2.5 tapped
    holes on a 23 mm square centred on the shaft.

The vendor file has the same datums with the shaft on -z: mounting face z = 0
(normal -z), pilot face z = -2, shaft tip z = -20, D-flat on y = +2 (normal
+y, 15 mm long), Ø2.05 tap holes at (±11.5, ±11.5) going +z, body back face
z = +44.5, and four Ø1 lead stubs leaving towards -y.  A half turn about Y,
(x, y, z) -> (-x, y, -z), therefore puts it in the PR #170 frame with no
translation: the pilot/shaft axis stays the z axis, the mounting face stays
z = 0, and the flat stays on +y.

Differences from PR #170's simplified stand-in (which this replaces): the real
body is 28.2 mm square with rounded corners and 44.5 mm long (PR #170: 28.0
square, 2.5 chamfers, 45.0 long), the tap holes are Ø2.05 x 4 deep (PR #170:
Ø2.5 x 2.5), and the vendor model carries end-cap details and lead stubs.
"""
from __future__ import annotations

from pathlib import Path

from cadgen import build123d as bd
from cadgen import read_step, srgb, step

REPO = Path(__file__).resolve().parents[4]
VENDOR_STEP = (REPO / "hardware" / "vendor-files" / "stepperonline-11hs18-0674s"
               / "cad" / "11HS18-0674S.STEP")

# Vendor frame -> PR #170 frame: the vendor x axis maps to -x, z to -z
# (y is kept), i.e. a 180 degree turn about Y, no translation.
VENDOR_X_IN_FRAME = (-1.0, 0.0, 0.0)
VENDOR_Z_IN_FRAME = (0.0, 0.0, -1.0)
VENDOR_ORIGIN_IN_FRAME = (0.0, 0.0, 0.0)

MOTOR_COLOR = "#3A3D42"        # black-anodised end caps / dark stator
LEADS_COLOR = "#1F1F1F"


@step(out="../../STEP/purchased/nema11.step")
def nema11():
    vendor = read_step(VENDOR_STEP)
    place = bd.Location(bd.Plane(origin=VENDOR_ORIGIN_IN_FRAME,
                                 x_dir=VENDOR_X_IN_FRAME, z_dir=VENDOR_Z_IN_FRAME))
    solids = sorted(vendor.solids(), key=lambda s: s.volume, reverse=True)
    # the motor (body, pilot and shaft) is one solid; the rest are lead stubs
    motor = place * solids[0]
    motor.label = "motor"
    motor.color = srgb(MOTOR_COLOR)
    leads = bd.Compound([place * s for s in sorted(solids[1:], key=lambda s: s.center().X)])
    leads.label = "leads"
    leads.color = srgb(LEADS_COLOR)
    return bd.Compound(children=[motor, leads], label="nema11")


if __name__ == "__main__":
    nema11()
