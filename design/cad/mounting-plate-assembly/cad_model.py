"""Hinged mounting-plate + baseplate assembly for the powder doser.

This module builds the parts requested in issue #58 ("Designing a complex
part with CADsmith"), pulling the upstream part dimensions from issues
#46 (auger bracket), #48 (geared auger + NEMA-17 drive), and #50 (tap
collar with hardstop). The pieces produced here are:

- ``mounting_plate``  : large upper plate that carries the auger's two
  brackets, the tap-collar mounting flange, and the NEMA-17 stepper.
  The plate hinges about an axis that intersects the auger's vertical
  discharge bore, so the whole top assembly can tilt 0°-90° without
  cutting the auger or any of its mounts.

- ``baseplate``       : lower plate carrying the mating hinge pillars,
  the lower (pivot) mount of a linear actuator, and four legs tall
  enough to sit a powder-collection cup on a scale underneath the
  discharge.

- Placeholder solids for the auger, brackets, tap collar, NEMA-17
  motor body, linear actuator (body + rod), cup, and scale, all of
  which are combined into a full STEP assembly so each printable part
  can be inspected in context.

The script is parametric: every dimension is a top-level constant so a
later CADsmith run (https://github.com/vertical-cloud-lab/CADSmith) can
re-author the same part shapes through its multi-agent loop without
having to re-discover the layout. CADsmith was the requested authoring
tool, but it depends on ``ANTHROPIC_API_KEY`` (see CADsmith README,
"Setup"), which is not provisioned in this sandbox; the part shapes
below are therefore written in the same CadQuery style CADsmith would
emit, so the geometry is drop-in compatible with a future CADsmith run.

Reproduce::

    pip install cadquery
    python design/cad/mounting-plate-assembly/cad_model.py
"""

from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq

# ---------------------------------------------------------------------------
# Coordinate system
# ---------------------------------------------------------------------------
# +X : auger long axis (motor end at +X, discharge end at X = 0)
# +Y : transverse (hinge axis is parallel to +Y at X = 0)
# +Z : up (away from baseplate, towards the auger when the assembly is at 0°)
# All dimensions are millimetres unless stated otherwise.

# ---------------------------------------------------------------------------
# Upstream part dimensions (from issues #46 / #48 / #50 / #24)
# ---------------------------------------------------------------------------
AUGER_OD = 25.0                  # outer diameter of the auger barrel (#46)
AUGER_LEN = 200.0                # nominal auger length
AUGER_DISCHARGE_BORE = 10.0      # vertical hole through the barrel near +X=0
AUGER_DISCHARGE_X = 18.0         # distance from auger end face to bore axis

BRACKET_FLANGE_W = 50.0          # mounting flange width  (#46)
BRACKET_FLANGE_D = 30.0          # mounting flange depth  (along auger axis)
BRACKET_HOLE_DX = 38.0           # M3 hole pattern along auger axis
BRACKET_HOLE_DY = 18.0           # M3 hole pattern transverse
BRACKET_HOLE_D = 3.4             # M3 clearance hole

TAP_PLATE_W = 50.0               # tap-collar mounting plate footprint
TAP_PLATE_D = 30.0
TAP_HOLE_DX = 38.0
TAP_HOLE_DY = 18.0
TAP_HOLE_D = 3.4

# NEMA-17 (per #24/#48): 42 x 42 body, 31 mm bolt circle, M3 mounting,
# 22 mm pilot boss, 5 mm output shaft.
NEMA17_BODY = 42.3
NEMA17_LEN = 48.0
NEMA17_BOLT_PITCH = 31.0
NEMA17_PILOT = 22.0 + 0.4        # +0.4 mm clearance for printed pocket
NEMA17_HOLE_D = 3.4              # M3 clearance
NEMA17_SHAFT_D = 5.2             # 5 mm shaft + 0.2 mm clearance

# Linear actuator placeholder (generic micro linear actuator).
LA_BODY_D = 30.0
LA_BODY_LEN = 150.0
LA_ROD_D = 12.0
LA_STROKE = 100.0
LA_PIN_D = 5.2                   # M5 clevis pin

# Cup + scale envelope (placeholders, sized to a typical bench scale).
SCALE_W, SCALE_D, SCALE_H = 130.0, 110.0, 28.0
CUP_OD, CUP_H = 60.0, 70.0

# ---------------------------------------------------------------------------
# Mounting plate
# ---------------------------------------------------------------------------
# The plate must be long enough to hold (motor end -> discharge end):
#   NEMA-17 mount  | bracket #2 | tap collar | bracket #1 | hinge end
# Bracket #1 sits just behind the discharge bore so the auger overhangs
# the hinge axis by AUGER_DISCHARGE_X.

MP_THK = 5.0                       # plate thickness
MP_WIDTH = 80.0                    # transverse footprint
MP_LEN = 250.0                     # X extent
# Plate sits this far above the auger axis so the auger and brackets clear
# the plate and the hinge pillars can rise alongside the auger without
# intersecting it. The brackets hang the auger BELOW the plate.
MP_OFFSET_ABOVE_AUGER = 0.0        # plate top surface is at the auger axis +
                                   # (AUGER_OD/2 + bracket flange thickness)
                                   # see BRACKET_FLANGE_T below.
BRACKET_FLANGE_T = 6.0             # thickness of the flange that bolts up
                                   # against the underside of the plate
PLATE_BOTTOM_Z = AUGER_OD / 2.0 + BRACKET_FLANGE_T   # underside Z
PLATE_TOP_Z = PLATE_BOTTOM_Z + MP_THK

# X positions of each mounted feature, measured from the discharge end (X=0).
X_BRACKET_DISCHARGE = 35.0         # bracket #1 (closest to discharge)
X_TAP_COLLAR = 95.0                # tap collar mount centre
X_BRACKET_MOTOR = 155.0            # bracket #2 (closest to motor)
X_NEMA17 = 215.0                   # NEMA-17 mount centre
# Auger bore at the discharge end is at X = AUGER_DISCHARGE_X (positive).
# Hinge axis lies in the YZ plane at X = AUGER_DISCHARGE_X.
HINGE_X = AUGER_DISCHARGE_X
HINGE_Z = 0.0                      # hinge axis is on the auger long axis
HINGE_PIN_D = 5.2                  # M5 clevis pin
HINGE_PILLAR_T = 6.0               # pillar thickness (Y direction)
HINGE_PILLAR_W = 14.0              # pillar width (X direction)
HINGE_PILLAR_H = (AUGER_OD / 2.0 + 6.0)   # pillar reaches from plate
                                          # underside down past the auger
HINGE_PILLAR_Y = AUGER_OD / 2.0 + 8.0     # pillar lateral offset from
                                          # auger centre (clears barrel)

# Discharge clearance: a U-notch in the +X (discharge) end of the plate so
# powder can fall straight down past the plate.
DISCHARGE_NOTCH_W = AUGER_OD + 6.0   # transverse opening
DISCHARGE_NOTCH_X = HINGE_X + 6.0    # how far the notch eats into the plate


def _mounting_plate_blank() -> cq.Workplane:
    """Top plate blank with rounded corners and the discharge notch."""
    plate = (
        cq.Workplane("XY")
        .box(MP_LEN, MP_WIDTH, MP_THK, centered=(False, True, False))
        .edges("|Z").fillet(6.0)
    )
    # Cut the discharge notch at the +X = 0 (discharge) end. Plate is built
    # from X=0 to X=MP_LEN (motor end at +X). The discharge end is X=0.
    notch = (
        cq.Workplane("XY")
        .box(DISCHARGE_NOTCH_X, DISCHARGE_NOTCH_W, MP_THK + 2,
             centered=(False, True, True))
    )
    plate = plate.cut(notch)
    return plate


def _add_bracket_holes(part: cq.Workplane, x_centre: float) -> cq.Workplane:
    """Add the four M3 mounting holes for one bracket flange."""
    pts = [
        (x_centre + dx, dy)
        for dx in (-BRACKET_HOLE_DX / 2.0, +BRACKET_HOLE_DX / 2.0)
        for dy in (-BRACKET_HOLE_DY / 2.0, +BRACKET_HOLE_DY / 2.0)
    ]
    return (
        part.faces(">Z").workplane(centerOption="CenterOfMass")
        .pushPoints(pts).hole(BRACKET_HOLE_D)
    )


def _add_tap_collar_holes(part: cq.Workplane, x_centre: float) -> cq.Workplane:
    pts = [
        (x_centre + dx, dy)
        for dx in (-TAP_HOLE_DX / 2.0, +TAP_HOLE_DX / 2.0)
        for dy in (-TAP_HOLE_DY / 2.0, +TAP_HOLE_DY / 2.0)
    ]
    return (
        part.faces(">Z").workplane(centerOption="CenterOfMass")
        .pushPoints(pts).hole(TAP_HOLE_D)
    )


def _add_nema17_holes(part: cq.Workplane, x_centre: float) -> cq.Workplane:
    """NEMA-17 pilot hole + four M3 clearance holes on a 31 mm pattern."""
    half = NEMA17_BOLT_PITCH / 2.0
    bolt_pts = [
        (x_centre + dx, dy)
        for dx in (-half, +half) for dy in (-half, +half)
    ]
    part = (
        part.faces(">Z").workplane(centerOption="CenterOfMass")
        .pushPoints(bolt_pts).hole(NEMA17_HOLE_D)
    )
    # Pilot boss / shaft pass-through.
    part = (
        part.faces(">Z").workplane(centerOption="CenterOfMass")
        .moveTo(x_centre, 0).hole(NEMA17_PILOT)
    )
    return part


def _add_hinge_pillars(part: cq.Workplane) -> cq.Workplane:
    """Add the two hinge pillars hanging below the plate at X = HINGE_X."""
    # Pillars hang DOWN from the plate underside. Each pillar is a thin
    # block straddling the auger; the pin axis is parallel to +Y, passes
    # through the auger's discharge bore axis (Z = HINGE_Z relative to the
    # auger centre, which is offset below the plate underside).
    auger_z_in_plate_frame = -(AUGER_OD / 2.0 + BRACKET_FLANGE_T)  # plate
    # underside is at z=0 in the plate's own local frame, the auger axis is
    # below by (AUGER_OD/2 + flange thickness).
    pillar_top_z = 0.0
    pillar_bot_z = auger_z_in_plate_frame - 6.0  # 6 mm below the auger
    pillar_h = pillar_top_z - pillar_bot_z

    for y_sign in (-1.0, +1.0):
        y_centre = y_sign * HINGE_PILLAR_Y
        pillar = (
            cq.Workplane("XY")
            .workplane(offset=pillar_bot_z)
            .center(HINGE_X, y_centre)
            .box(HINGE_PILLAR_W, HINGE_PILLAR_T, pillar_h,
                 centered=(True, True, False))
        )
        # Drill the hinge pin hole through the pillar at the auger axis Z.
        pin_z = auger_z_in_plate_frame  # pin coincident with auger long axis
        pillar = (
            pillar.faces(f"{'<' if y_sign > 0 else '>'}Y")
            .workplane(centerOption="CenterOfMass")
            .center(0, pin_z - (pillar_bot_z + pillar_h / 2.0))
            .hole(HINGE_PIN_D)
        )
        part = part.union(pillar)

    # Attach the linear-actuator clevis tab to the underside of the plate
    # CLOSE to the hinge (small lever arm → modest LA stroke). Tab is a
    # thin Y-aligned plate with a single M5 clevis hole.
    tab_x = HINGE_X + 55.0     # 55 mm out from the hinge along the auger
    tab_w = 16.0
    tab_t = 6.0
    tab_h = 22.0
    tab_z_top = 0.0
    tab_z_bot = -tab_h
    tab = (
        cq.Workplane("XY")
        .workplane(offset=tab_z_bot)
        .center(tab_x, 0)
        .box(tab_w, tab_t, tab_h, centered=(True, True, False))
        .faces("<Y").workplane(centerOption="CenterOfMass")
        .center(0, (tab_h / 2.0) - 5.0)
        .hole(LA_PIN_D)
    )
    part = part.union(tab)
    return part


def build_mounting_plate() -> cq.Workplane:
    plate = _mounting_plate_blank()
    plate = _add_bracket_holes(plate, X_BRACKET_DISCHARGE)
    plate = _add_tap_collar_holes(plate, X_TAP_COLLAR)
    plate = _add_bracket_holes(plate, X_BRACKET_MOTOR)
    plate = _add_nema17_holes(plate, X_NEMA17)
    plate = _add_hinge_pillars(plate)
    return plate


# ---------------------------------------------------------------------------
# Baseplate
# ---------------------------------------------------------------------------
BP_THK = 6.0
BP_WIDTH = 200.0
BP_LEN = 300.0          # spans hinge end to actuator end
LEG_H = 150.0            # legs tall enough to fit a 28 mm scale + 70 mm cup
LEG_SECTION = 18.0       # leg cross-section (square tube)

# Baseplate origin: same X axis as mounting plate, but baseplate is centred
# in Y (about the auger). The baseplate is positioned so the hinge end of
# the mounting plate sits over the baseplate's hinge pillars.
BP_X_OFFSET = -30.0     # baseplate extends from X = -30 (past the hinge)
                         # to X = BP_LEN + BP_X_OFFSET = 270
HINGE_X_BASE = HINGE_X   # mating hinge pillars at the same X as MP hinge

# Linear actuator base pivot is on the baseplate at +X end.
LA_BASE_PIVOT_X = HINGE_X + 130.0    # base pivot well past the tab so the
                                     # actuator pulls the plate down at 0°
                                     # and pushes it up at 90°
# Actuator base pivot Z (above the baseplate top surface) is set so that
# at 0° tilt the actuator rod is fully retracted; the geometry is captured
# in render_views.py / diagrams.

# Discharge cut-out: a rectangular hole in the baseplate directly below the
# discharge so powder falls through onto the cup.
DISCHARGE_OPENING_W = 70.0
DISCHARGE_OPENING_D = 70.0


def build_baseplate() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .box(BP_LEN, BP_WIDTH, BP_THK,
             centered=(False, True, False))
        .translate((BP_X_OFFSET, 0, 0))
        .edges("|Z").fillet(8.0)
    )

    # Discharge cut-out below the auger discharge bore.
    cut = (
        cq.Workplane("XY")
        .box(DISCHARGE_OPENING_D, DISCHARGE_OPENING_W, BP_THK + 2,
             centered=(True, True, True))
        .translate((HINGE_X, 0, BP_THK / 2.0))
    )
    plate = plate.cut(cut)

    # Mating hinge pillars rising UP from the baseplate.
    base_pillar_h = LEG_H * 0.0 + (
        # pillars must reach up to the auger axis (= mounting plate hinge
        # pin Z when assembly is at 0°). When the mounting plate sits on
        # top of the baseplate hinge pillars, the pin Z (in baseplate
        # frame) is BP_THK + base_pillar_h.
        # We choose base_pillar_h so the pin is at:
        #   z_pin = BP_THK + base_pillar_h  (relative to baseplate top)
        # and the mounting plate's auger axis is exactly there.
        50.0
    )
    for y_sign in (-1.0, +1.0):
        y_centre = y_sign * (HINGE_PILLAR_Y + HINGE_PILLAR_T + 1.0)
        pillar = (
            cq.Workplane("XY")
            .workplane(offset=BP_THK)
            .center(HINGE_X, y_centre)
            .box(HINGE_PILLAR_W, HINGE_PILLAR_T,
                 base_pillar_h, centered=(True, True, False))
        )
        # Drill hinge pin hole at the same world-Z as the mounting plate
        # pin (pin_z = BP_THK + base_pillar_h).
        face = "<Y" if y_sign > 0 else ">Y"
        pillar = (
            pillar.faces(face).workplane(centerOption="CenterOfMass")
            .center(0, base_pillar_h / 2.0 - 4.0)
            .hole(HINGE_PIN_D)
        )
        plate = plate.union(pillar)

    # Linear-actuator base pivot: a small clevis on the baseplate top
    # surface, M5 pin, at LA_BASE_PIVOT_X.
    clevis_h = 25.0
    for y_sign in (-1.0, +1.0):
        clevis = (
            cq.Workplane("XY")
            .workplane(offset=BP_THK)
            .center(LA_BASE_PIVOT_X, y_sign * 8.0)
            .box(14.0, 4.0, clevis_h, centered=(True, True, False))
            .faces("<Y" if y_sign > 0 else ">Y")
            .workplane(centerOption="CenterOfMass")
            .center(0, clevis_h / 2.0 - 5.0)
            .hole(LA_PIN_D)
        )
        plate = plate.union(clevis)

    # Four legs at the baseplate corners.
    bp_x0 = BP_X_OFFSET
    bp_x1 = BP_X_OFFSET + BP_LEN
    bp_y0 = -BP_WIDTH / 2.0
    bp_y1 = +BP_WIDTH / 2.0
    inset = LEG_SECTION / 2.0 + 4.0
    leg_pts = [
        (bp_x0 + inset, bp_y0 + inset),
        (bp_x0 + inset, bp_y1 - inset),
        (bp_x1 - inset, bp_y0 + inset),
        (bp_x1 - inset, bp_y1 - inset),
    ]
    for (lx, ly) in leg_pts:
        leg = (
            cq.Workplane("XY")
            .workplane(offset=-LEG_H)
            .center(lx, ly)
            .box(LEG_SECTION, LEG_SECTION, LEG_H + BP_THK,
                 centered=(True, True, False))
        )
        plate = plate.union(leg)

    # Cross-brace holes (M4) at the bottom of each leg so the user can
    # bolt on a horizontal stiffening rail later if needed.
    for (lx, ly) in leg_pts:
        side_face = "<X" if lx < 0 else ">X"
        try:
            plate = (
                plate.faces(side_face).workplane(centerOption="CenterOfMass",
                                                 origin=(lx, ly, -LEG_H + 15.0))
                .hole(4.4)
            )
        except Exception:
            # Multi-face selection edge case; safe to skip the optional
            # cross-brace hole rather than abort the whole part.
            pass

    return plate


# ---------------------------------------------------------------------------
# Placeholder companion solids (for the assembly STEP)
# ---------------------------------------------------------------------------

def build_auger() -> cq.Workplane:
    """Cylindrical auger barrel + vertical discharge bore at +X end."""
    auger = (
        cq.Workplane("YZ")
        .circle(AUGER_OD / 2.0)
        .extrude(AUGER_LEN)
    )
    # Drill the discharge bore: vertical cylinder through the barrel.
    bore = (
        cq.Workplane("XY")
        .circle(AUGER_DISCHARGE_BORE / 2.0)
        .extrude(AUGER_OD + 2.0)
        .translate((AUGER_DISCHARGE_X, 0, -AUGER_OD / 2.0 - 1.0))
    )
    auger = auger.cut(bore)
    return auger


def build_bracket() -> cq.Workplane:
    """Crude split-collar + flange bracket placeholder."""
    flange = (
        cq.Workplane("XY")
        .box(BRACKET_FLANGE_D, BRACKET_FLANGE_W, BRACKET_FLANGE_T,
             centered=(True, True, False))
    )
    # Add the collar around the auger.
    collar_od = AUGER_OD + 12.0
    collar = (
        cq.Workplane("YZ")
        .circle(collar_od / 2.0)
        .circle(AUGER_OD / 2.0 + 0.3)  # 0.3 mm radial clearance
        .extrude(BRACKET_FLANGE_D, both=True)
        .translate((0, 0, -(AUGER_OD / 2.0 + BRACKET_FLANGE_T)))
    )
    # Position the flange so it sits ABOVE the auger, with its top face
    # kissing the mounting plate's underside (auger axis is at z=0 in the
    # bracket's local frame; plate underside is at z = AUGER_OD/2 +
    # BRACKET_FLANGE_T). Flange occupies z = AUGER_OD/2 .. AUGER_OD/2 +
    # BRACKET_FLANGE_T.
    flange = flange.translate((0, 0, AUGER_OD / 2.0))
    return flange.union(collar)


def build_tap_collar_mount() -> cq.Workplane:
    """Tap-collar mounting plate with hardstop column (placeholder)."""
    flange = (
        cq.Workplane("XY")
        .box(TAP_PLATE_D, TAP_PLATE_W, BRACKET_FLANGE_T,
             centered=(True, True, False))
        .translate((0, 0, AUGER_OD / 2.0))
    )
    # Hardstop column hangs DOWN from the flange to contact the rotating
    # collar; placed beside the auger so it does not interfere with it.
    column = (
        cq.Workplane("XY")
        .box(8.0, 8.0, AUGER_OD,
             centered=(True, True, False))
        .translate((0, AUGER_OD / 2.0 + 6.0, -AUGER_OD / 2.0))
    )
    return flange.union(column)


def build_nema17() -> cq.Workplane:
    body = (
        cq.Workplane("XY")
        .box(NEMA17_BODY, NEMA17_BODY, NEMA17_LEN, centered=(True, True, False))
    )
    shaft = (
        cq.Workplane("XY")
        .circle(NEMA17_SHAFT_D / 2.0).extrude(20.0)
        .translate((0, 0, NEMA17_LEN))
    )
    return body.union(shaft)


def build_linear_actuator() -> cq.Workplane:
    body = (
        cq.Workplane("XY")
        .circle(LA_BODY_D / 2.0).extrude(LA_BODY_LEN)
    )
    rod = (
        cq.Workplane("XY")
        .circle(LA_ROD_D / 2.0).extrude(LA_STROKE)
        .translate((0, 0, LA_BODY_LEN))
    )
    # Clevis lugs at each end (simplified).
    lug_a = cq.Workplane("XY").box(20.0, 8.0, 8.0).translate((0, 0, -4.0))
    lug_b = (
        cq.Workplane("XY").box(20.0, 8.0, 8.0)
        .translate((0, 0, LA_BODY_LEN + LA_STROKE + 4.0))
    )
    return body.union(rod).union(lug_a).union(lug_b)


def build_cup() -> cq.Workplane:
    return (
        cq.Workplane("XY").circle(CUP_OD / 2.0).extrude(CUP_H)
        .faces(">Z").workplane().circle(CUP_OD / 2.0 - 2.0).cutBlind(-CUP_H + 2.0)
    )


def build_scale() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(SCALE_W, SCALE_D, SCALE_H, centered=(True, True, False))
        .edges("|Z").fillet(4.0)
    )


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def build_assembly(tilt_deg: float = 0.0) -> cq.Assembly:
    """Full assembly with the upper mounting plate tilted by ``tilt_deg``.

    The hinge axis is parallel to +Y at world point (HINGE_X, 0, pin_z),
    where pin_z is the height of the hinge pin above the baseplate top
    surface (pin_z = BP_THK + base_pillar_h, see ``build_baseplate``).
    """
    base_pillar_h = 50.0
    pin_world_z = BP_THK + base_pillar_h - LEG_H + 0.0
    # We treat the world Z=0 as the FLOOR (i.e. the bottoms of the legs).
    # That puts the baseplate top surface at world z = LEG_H + BP_THK,
    # and the hinge pin at world z = LEG_H + BP_THK + base_pillar_h - 4.0
    # (4 mm down from the pillar tops, matching the hole offset).
    pin_world_z = LEG_H + BP_THK + base_pillar_h - 4.0
    # Build a transform that rotates the upper sub-assembly about the
    # hinge pin axis (parallel to -Y, so that +X end rotates UP to +Z;
    # otherwise the motor would swing down and collide with the
    # baseplate).
    tilt = cq.Location(
        cq.Vector(HINGE_X, 0, pin_world_z),
        cq.Vector(0, -1, 0),
        tilt_deg,
    )
    # The mounting plate's underside (in its own frame) is at z = 0 and
    # the auger axis is at z = -(AUGER_OD/2 + BRACKET_FLANGE_T). To put
    # the auger axis at the hinge pin Z, raise the mounting plate by
    # +(AUGER_OD/2 + BRACKET_FLANGE_T) and shift it so the hinge pillars
    # straddle X = HINGE_X.
    mp_z_lift = (AUGER_OD / 2.0 + BRACKET_FLANGE_T)
    mp_loc = cq.Location(cq.Vector(0, 0, pin_world_z + mp_z_lift))

    # Auger frame: same lift, X already laid out so X=0 is the discharge
    # end. Translate auger so its discharge bore is at HINGE_X.
    auger_loc = cq.Location(cq.Vector(0, 0, pin_world_z))

    # Bracket placement: each bracket sits at its X centre and is anchored
    # to the auger axis (z = pin_world_z) with its flange against the
    # mounting plate underside.
    def bracket_loc(x_centre: float) -> cq.Location:
        return cq.Location(cq.Vector(x_centre, 0, pin_world_z))

    nema_loc = cq.Location(
        cq.Vector(X_NEMA17, 0,
                  pin_world_z + mp_z_lift + MP_THK)  # motor sits ON TOP
    )

    # Linear actuator: pin lower lug to baseplate clevis (LA_BASE_PIVOT_X,
    # 0, BP top + 12). Pin upper lug to mounting plate tab (MP_LEN-30,
    # 0, plate underside - 17). Render at 0° tilt as a vertical column for
    # simplicity; rotation diagrams use the full math.
    la_lower_x = LA_BASE_PIVOT_X
    la_lower_z = LEG_H + BP_THK + 12.0
    la_upper_z = pin_world_z + mp_z_lift - 17.0
    la_dx = (HINGE_X + 55.0) - la_lower_x   # tab_x is HINGE_X+55 (see
                                             # mounting-plate hinge code)
    la_dz = la_upper_z - la_lower_z
    la_len_actual = math.hypot(la_dx, la_dz)
    la_pitch_deg = math.degrees(math.atan2(la_dx, la_dz))
    la_loc = cq.Location(
        cq.Vector(la_lower_x, 0, la_lower_z),
        cq.Vector(0, 1, 0),
        la_pitch_deg,
    )
    # We don't auto-resize the actuator solid; just rotate the standard
    # one. The placeholder is long enough that a small overhang is fine.
    _ = la_len_actual

    base_loc = cq.Location(cq.Vector(0, 0, LEG_H))

    cup_loc = cq.Location(cq.Vector(HINGE_X, 0, 0.0))
    scale_loc = cq.Location(cq.Vector(HINGE_X, 0, 0.0))

    # Build the upper sub-assembly first, then nest it under the tilt.
    upper = cq.Assembly(name="upper")
    upper.add(build_mounting_plate(), name="mounting_plate", loc=mp_loc,
              color=cq.Color(0.85, 0.85, 0.95))
    upper.add(build_auger(), name="auger", loc=auger_loc,
              color=cq.Color(0.55, 0.40, 0.20))
    for label, x in (
        ("bracket_discharge", X_BRACKET_DISCHARGE),
        ("bracket_motor", X_BRACKET_MOTOR),
    ):
        upper.add(build_bracket(), name=label, loc=bracket_loc(x),
                  color=cq.Color(0.90, 0.65, 0.20))
    upper.add(build_tap_collar_mount(), name="tap_collar_mount",
              loc=bracket_loc(X_TAP_COLLAR),
              color=cq.Color(0.65, 0.30, 0.30))
    upper.add(build_nema17(), name="nema17", loc=nema_loc,
              color=cq.Color(0.20, 0.20, 0.22))

    full = cq.Assembly(name="powder_doser")
    full.add(upper, name="tilting_head", loc=tilt)
    full.add(build_baseplate(), name="baseplate", loc=base_loc,
             color=cq.Color(0.80, 0.80, 0.80))
    full.add(build_linear_actuator(), name="linear_actuator", loc=la_loc,
             color=cq.Color(0.30, 0.45, 0.70))
    full.add(build_scale(), name="scale", loc=scale_loc,
             color=cq.Color(0.25, 0.25, 0.25))
    full.add(build_cup(),
             name="cup",
             loc=cq.Location(cq.Vector(HINGE_X, 0, SCALE_H + 1.0)),
             color=cq.Color(0.95, 0.95, 0.65))
    return full


# ---------------------------------------------------------------------------
# Export entrypoint
# ---------------------------------------------------------------------------
HERE = Path(__file__).parent
STEP_DIR = HERE / "step"
STL_DIR = HERE / "stl"


def _export_part(part: cq.Workplane, name: str) -> None:
    STEP_DIR.mkdir(exist_ok=True)
    STL_DIR.mkdir(exist_ok=True)
    cq.exporters.export(part, str(STEP_DIR / f"{name}.step"))
    cq.exporters.export(part, str(STL_DIR / f"{name}.stl"),
                        tolerance=0.05, angularTolerance=0.2)


def main() -> None:
    print("Building mounting plate ...")
    mp = build_mounting_plate()
    _export_part(mp, "mounting_plate")
    print("Building baseplate ...")
    bp = build_baseplate()
    _export_part(bp, "baseplate")
    print("Building auger / bracket / tap-collar / NEMA-17 / actuator / "
          "cup / scale placeholders ...")
    for solid, name in (
        (build_auger(), "auger_placeholder"),
        (build_bracket(), "bracket_placeholder"),
        (build_tap_collar_mount(), "tap_collar_mount_placeholder"),
        (build_nema17(), "nema17_placeholder"),
        (build_linear_actuator(), "linear_actuator_placeholder"),
        (build_cup(), "cup_placeholder"),
        (build_scale(), "scale_placeholder"),
    ):
        _export_part(solid, name)
    print("Building full assembly ...")
    asm = build_assembly(tilt_deg=0.0)
    asm.save(str(STEP_DIR / "assembly_0deg.step"))
    asm45 = build_assembly(tilt_deg=45.0)
    asm45.save(str(STEP_DIR / "assembly_45deg.step"))
    asm90 = build_assembly(tilt_deg=90.0)
    asm90.save(str(STEP_DIR / "assembly_90deg.step"))
    print("Done.")


if __name__ == "__main__":
    main()
