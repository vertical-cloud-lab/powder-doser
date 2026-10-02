"""Parametric tap-collar assembly for the Powder Doser auger.

The tap collar is the third printed part in the part-by-part Powder Doser
build (after the auger of PR #16 and the auger bracket of PR #47).  It is
made of two independent printed pieces that are not rigidly attached to
each other or to the chassis baseplate:

* **Mounting plate** — a rectangular flange that bolts to the chassis with
  four corner M3 screws (same footprint and corner-hole pattern as the
  auger bracket).  Instead of a circular collar it has a small *hardstop
  bump* on the +X end of the plate top.  The bump's top face sits a hair
  below the bottom face of the collar's lower clamp tab at rest, so that
  as the auger tries to drag the collar around with it the lower tab
  presses down on the bump and rotation is arrested with the tabs
  horizontal.  The bump straddles the +X corner mount screw (a Ø3.4
  cylindrical cut-out through the bump lets the M3 pass straight through)
  so the bump can be wide and structurally robust without losing
  screwdriver access.
* **Tap collar** — a split shaft-collar (same bore / OD / clamp-slot /
  clamp-ear geometry as the auger bracket) that wraps around the auger
  with a free-running fit.  The clamp slot is rotated 90° from the
  bracket so the slot opens to the +X side and the two clamp ears form a
  pair of *contact-point tabs* whose horizontal rest orientation is
  defined by the mounting-plate bump beneath the lower tab.  The collar
  is longer along the auger axis than the bracket (24 mm vs 12 mm) so
  there is solid material beneath the full solenoid mounting boss, with
  every mounting hole sitting fully over collar wall rather than
  being cantilevered into mid-air.  The collar also carries:

    - a flat *side pad* on the -X side for adhesive-mounting a Ø10 mm
      coin vibration motor, and
    - a flat *top boss* on the +Z side with the real Adafruit 412 /
      TAU0730TM push/pull solenoid's two diagonal M3 mounting holes
      (18.2 mm pitch in X, 16.0 mm in Y) plus a plunger-clearance hole
      through the collar wall so the solenoid plunger can tap the auger
      directly.

  Both mounting features are built as *tapered wedges* whose base flares
  out wider than the mounting face and merges into the collar OD,
  forming integral gussets so the pads aren't fragile flat plates
  hanging off the cylinder.

The collar is meant to spin freely on the auger (the clamp screw lets you
adjust the running fit but is not torqued down), while the bump on the
mounting plate keeps it from being dragged around with the auger and
winding up the motor / solenoid wiring.

Bore, collar OD, clamp slot, clamp-ear and corner-mount-hole dimensions
deliberately match the bracket from PR #47 so the same M3 hardware and
the same Ø25 mm Archimedes auger from PR #16 are reused.

Run from the package directory to (re)generate STEP + per-part STLs::

    cd design/cad/tap-collar
    python cad_model.py
"""

from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq

# ---------------------------------------------------------------------------
# Shared parameters (mm) — kept in sync with design/cad/auger-bracket
# ---------------------------------------------------------------------------
AUGER_OD = 25.0
BORE_CLEARANCE = 0.5             # diametral, free-running fit on FDM
BORE_D = AUGER_OD + BORE_CLEARANCE  # = 25.5 mm

COLLAR_WALL = 4.0
COLLAR_OD = BORE_D + 2 * COLLAR_WALL  # = 33.5 mm

# Plate footprint and corner mount holes — identical to the bracket so the
# tap-collar mounting plate drops into the same chassis hole pattern.
PLATE_LENGTH = 60.0              # X
PLATE_DEPTH = 24.0               # Y (along the auger axis) — matched to
                                 # TC_COLLAR_DEPTH so the mount plate is the
                                 # same width as the tap collar along the
                                 # auger axis (PR #51 v4 feedback from Will;
                                 # was 12 mm in v1-v3, inherited from the
                                 # bracket footprint in PR #47; bumped 18→24
                                 # in v6 so the real Adafruit 412 / TAU0730TM
                                 # solenoid mount-hole pattern fits — see
                                 # TC_COLLAR_DEPTH).
PLATE_THICKNESS = 14.0           # Z (lifted to clear the PR #49 gear OD)

MOUNT_HOLE_D = 3.4               # M3 clearance through-hole
MOUNT_HOLE_INSET_X = 6.0         # from each plate end (X) to hole centre
MOUNT_HOLE_INSET_Y = 6.0         # from each plate side (Y) to hole centre

# Bore-axis Z above the plate bottom — kept identical to the bracket so the
# tap collar sits at the same height on the chassis as the brackets.
COLLAR_PLATE_OVERLAP = 1.5
COLLAR_CENTRE_Z = PLATE_THICKNESS + COLLAR_OD / 2 - COLLAR_PLATE_OVERLAP
COLLAR_TOP_Z = COLLAR_CENTRE_Z + COLLAR_OD / 2

# Collar Y-extent (along the auger axis).  Lengthened from the bracket's
# 12 mm so the full solenoid mounting boss sits over solid collar wall
# (rather than letting the screw holes cantilever off the boss into
# mid-air, per PR review).  PLATE_DEPTH is matched to this so the mount
# plate is the same width as the tap collar along the auger axis (PR #51
# v4 feedback from Will).  v7: bumped 18 → 24 mm so the *real* push/pull
# solenoid (Adafruit 412 / TAU0730TM) mounting-hole pattern fits — its two
# mount holes are 16.0 mm apart along the auger axis (vs the 12 mm pitch
# the v1-v5 boss assumed), which needs a wider collar to keep both holes
# over solid material (Will's print-fit comment, PR #51 4672498176).
TC_COLLAR_DEPTH = 24.0
assert PLATE_DEPTH == TC_COLLAR_DEPTH, (
    "PLATE_DEPTH must match TC_COLLAR_DEPTH so the mount plate is the "
    "same width as the tap collar along the auger axis."
)

# Top clamp tabs (the two ears separated by the clamp slot).  Same Z height
# and clamp-screw centring rule as the bracket; tabs are widened along the
# slot-open direction (here X) so they double as the hardstop "contact
# point" reaching out over the mounting-plate bump.
CLAMP_GAP = 2.0                  # clamp slot width (drawing callout)
CLAMP_SCREW_D = 3.4              # M3 clearance through both tabs

# Bracket TOP_TAB_W is 3 mm; here we widen the tabs along their projection
# axis to TC_TAB_W = 8 mm so they reach over the +X hardstop bump.
# TC_TAB_H matches the bracket so the M3 clamp screw hole still has
# ~1.8 mm of wall above and below it.
TC_TAB_W = 8.0                   # tab length along the slot-open direction
TC_TAB_H = 7.0                   # tab thickness perpendicular to the slot
TAB_COLLAR_OVERLAP = 6.0         # how far the tab block sinks into the collar

# Fillets — same recipe as the bracket.
FILLET_TAB_COLLAR = 1.0
FILLET_TAB_TOP = 1.0
FILLET_PLATE_BUMP = 1.5

# ---------------------------------------------------------------------------
# Mounting-plate-only parameters: hardstop bump
# ---------------------------------------------------------------------------
# Hardstop bump on the +X end of the plate top.  Geometry (per PR review):
#   * Top face sits a hair below the resting bottom face of the lower
#     clamp tab — at rest the tab rests on (or just above) the bump, and
#     CCW rotation of the collar is immediately arrested.
#   * X-range is wide enough to be structurally robust *and* to overlap
#     the +X corner mount hole at X = 24 mm.  A Ø3.4 cylindrical cut-out
#     through the bump preserves M3 screwdriver access (the "hollow"
#     option the reviewer called out).
#   * Stays *below* the lower-tab Z range at rest — no interference with
#     the collar when installing it onto the auger.
LOWER_TAB_BOTTOM_Z = COLLAR_CENTRE_Z - CLAMP_GAP / 2 - TC_TAB_H  # = 21.25 mm
BUMP_TOP_GAP = 0.25              # vertical gap between bump top and tab
BUMP_TOP_Z = LOWER_TAB_BOTTOM_Z - BUMP_TOP_GAP                    # = 21.00 mm
BUMP_HEIGHT = BUMP_TOP_Z - PLATE_THICKNESS                        # = 7.00 mm
# Inner face of the bump sits just outboard of the collar OD; outer face
# extends past the +X mount hole so the bump straddles the screw.  The
# Ø3.4 cut-out through the bump body keeps the screw accessible.
BUMP_INNER_X = COLLAR_OD / 2 + 0.5                                # = 17.25 mm
BUMP_OUTER_X = (PLATE_LENGTH / 2 - MOUNT_HOLE_INSET_X) + MOUNT_HOLE_D / 2 + 1.5
                                                                  # = 27.20 mm
BUMP_DEPTH = PLATE_DEPTH                                           # full plate Y

# M3 countersink (90° included angle, standard ISO 10642 flat-head) for the
# +X corner mount screw — sunk into the bump top so the bump's top face
# stays flat once the screw is installed (PR review v3 feedback).
CSK_HEAD_D = 6.0                 # M3 flat-head OD across the rim
CSK_INCLUDED_ANGLE_DEG = 90.0    # ISO 10642 / DIN 7991 default
# Depth from top surface to the point where the cone reaches MOUNT_HOLE_D.
# tan(45°) = 1, so depth = (head_d - hole_d) / 2 for a 90° included angle.
CSK_DEPTH = (CSK_HEAD_D - MOUNT_HOLE_D) / 2 / math.tan(
    math.radians(CSK_INCLUDED_ANGLE_DEG / 2)
)                                # = 1.30 mm

assert BUMP_OUTER_X <= PLATE_LENGTH / 2, (
    "Hardstop bump extends past the plate end."
)
assert BUMP_TOP_Z < LOWER_TAB_BOTTOM_Z, (
    "Hardstop bump top would interfere with the lower clamp tab at rest."
)
assert CSK_DEPTH < BUMP_HEIGHT, (
    "Countersink for the +X mount screw is deeper than the hardstop bump."
)

# ---------------------------------------------------------------------------
# Mounting-plate collar relief (per PR review v3)
# ---------------------------------------------------------------------------
# The tap collar must spin freely above the mounting plate, but the
# collar's cylindrical body sits 1.5 mm into the plate at rest (the
# COLLAR_PLATE_OVERLAP that the bracket fillets into a tangent blend).
# For the *bracket* that is fine because the bracket and collar are one
# rigid part; for the *tap collar* this overlap is direct mechanical
# interference between two parts that must rotate relative to each other.
#
# Cut a cylindrical relief into the mounting-plate top that gives the
# collar OD the same 0.5 mm diametral free-running clearance as the bore
# uses on the auger (matching the PR #46 / #47 bracket convention).
COLLAR_RELIEF_CLEARANCE = 0.5    # diametral, same fit as BORE_CLEARANCE
COLLAR_RELIEF_R = COLLAR_OD / 2 + COLLAR_RELIEF_CLEARANCE / 2  # = 17.00 mm
COLLAR_RELIEF_DEPTH_OVERSHOOT = 1.0  # extend the cylinder past the Y faces
                                     # of the plate to guarantee through-cut

# ---------------------------------------------------------------------------
# Tap-collar-only parameters: coin-motor side pad and solenoid top boss
# ---------------------------------------------------------------------------
# Both mounting features are now built as full *rectangular slabs* that
# sink deeply into the collar OD, with the collar-cylinder/slab
# intersection blended by a fillet — mirroring the bracket-plate ↔ collar
# template from PR #46 / #47 (where the collar dips into the plate by
# COLLAR_PLATE_OVERLAP = 1.5 mm and a 3 mm fillet smooths the
# intersection).  This replaces the v2 tapered-wedge approach, which
# left a weak point right at the cylinder/face intersection (per PR
# review: "directly at the intersection of the plates and the collar
# circle there is a weak point — make it look like the mounting plates
# are coming out of the collar, a rectangle, not a line and a circle").
PAD_COLLAR_OVERLAP = 3.0         # how deep each slab sinks into the collar OD
FILLET_PAD_COLLAR = 1.5          # blend at the slab/collar intersection

# Coin vibration motor (e.g. 10 mm Ø × 3 mm thick adhesive coin motor).
# Slab on the -X side of the collar with a shallow circular recess on the
# mounting face for adhesive location.
COIN_MOTOR_D = 10.0
COIN_MOTOR_RECESS_DEPTH = 1.0
COIN_PAD_W = 14.0                # Z-extent of the rectangular slab
COIN_PAD_DEPTH = TC_COLLAR_DEPTH # Y-extent (full collar length)
COIN_PAD_PROUD = 1.0             # how far the flat face sits outboard of
                                 # the collar OD's tangent at -X

# Push/pull solenoid — the real part now in hand is a small open-frame
# push/pull solenoid (Adafruit 412 / Shanghai Chaocheng TAU0730TM, 12 V,
# 51.9 mm long incl. plunger, 29.7 mm body, 14 × 17 mm cross-section,
# Ø5 plunger cap, Ø6.9 plunger bushing).  Its mounting flange has TWO
# screw holes (≈ Ø3, M3) on diagonally-opposite ears, not the two
# symmetric M2 holes the v1-v5 boss assumed:
#
#       18.2 ±0.05 mm apart across the body  (SOLENOID_HOLE_PITCH_ACROSS)
#       16.0      mm apart along the body     (SOLENOID_HOLE_PITCH_ALONG)
#
# The mounting boss is a rectangular reinforced slab on +Z, but the
# plunger axis is oriented along X so it is perpendicular to the auger
# axis (Y).  The plunger path is set so the extended tip reaches 3 mm
# into the auger OD.  Source: Adafruit 412 datasheet
# 412_C514-B_diagram.PDF (PR #51 4672498176).
SOLENOID_BOSS_W = 24.0           # X-extent of the rectangular slab — wide
                                 # enough to carry the X = ±9.1 mm holes
SOLENOID_BOSS_DEPTH = TC_COLLAR_DEPTH  # Y-extent (full collar length)
SOLENOID_BOSS_PROUD = 4.0        # how far the boss sits proud of COLLAR_TOP_Z
                                 # (raised from 2 mm so the M3 mount holes
                                 # have enough slab depth to thread into)
SOLENOID_SCREW_D = 2.7           # self-tapping pilot for an M3 screw driven
                                 # through the solenoid's Ø3 flange holes
                                 # into the printed boss
SOLENOID_HOLE_PITCH_ACROSS = 18.2  # mount-hole pitch across the body
SOLENOID_HOLE_PITCH_ALONG = 16.0   # mount-hole pitch along the body axis
SOLENOID_PLUNGER_D = 7.5         # plunger clearance hole through the wall —
                                 # opened from Ø6 to clear the Ø6.9 plunger
                                 # bushing (Max 0.5 mm proud) of the real part
SOLENOID_INTERFERENCE_INTO_AUGER = 3.0  # extended tip depth into auger OD

# Mount-hole centres (diagonally opposite ears, plunger centred between).
SOLENOID_HOLE_OFFSETS = (
    (+SOLENOID_HOLE_PITCH_ALONG / 2, +SOLENOID_HOLE_PITCH_ACROSS / 2),
    (-SOLENOID_HOLE_PITCH_ALONG / 2, -SOLENOID_HOLE_PITCH_ACROSS / 2),
)

# Sanity check: the diagonal mount holes must clear the central plunger
# hole.
_hole_centre_dist = math.hypot(
    SOLENOID_HOLE_PITCH_ALONG / 2, SOLENOID_HOLE_PITCH_ACROSS / 2
)
assert _hole_centre_dist - SOLENOID_SCREW_D / 2 > SOLENOID_PLUNGER_D / 2 + 0.5, (
    "Solenoid mount holes overlap the plunger clearance hole."
)
# Sanity check: mount holes must stay inside the boss footprint with at
# least 1 mm of edge wall, in both X and Y.
assert (
    SOLENOID_HOLE_PITCH_ALONG / 2 + SOLENOID_SCREW_D / 2 + 1.0
    <= SOLENOID_BOSS_W / 2
), (
    "Solenoid mount holes fall outside the boss footprint in X."
)
assert (
    SOLENOID_HOLE_PITCH_ACROSS / 2 + SOLENOID_SCREW_D / 2 + 1.0
    <= SOLENOID_BOSS_DEPTH / 2
), (
    "Solenoid mount holes fall outside the boss footprint in Y."
)
# Sanity check: the mount holes must sit fully *inside* the collar
# Y-extent (the v1 bug was that the holes hung off the 12 mm bracket-depth
# collar; the real solenoid's 18.2 mm across-body pitch needs the v7 24 mm collar).
assert (
    SOLENOID_HOLE_PITCH_ACROSS / 2 + SOLENOID_SCREW_D / 2 + 1.0
    <= TC_COLLAR_DEPTH / 2
), (
    "Solenoid mount holes hang off the collar Y-extent — "
    "increase TC_COLLAR_DEPTH."
)
assert 0.0 < SOLENOID_INTERFERENCE_INTO_AUGER < AUGER_OD / 2, (
    "SOLENOID_INTERFERENCE_INTO_AUGER must be between 0 and AUGER_OD/2."
)
assert AUGER_OD / 2 - SOLENOID_INTERFERENCE_INTO_AUGER < BORE_D / 2, (
    "Plunger target point must reach into the collar bore."
)
# Sanity check: pad overlap must be smaller than the collar wall, or the
# slab cuts through into the bore.
assert PAD_COLLAR_OVERLAP < COLLAR_WALL, (
    "PAD_COLLAR_OVERLAP would cut through the collar wall into the bore."
)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------
def build_mount_plate() -> cq.Workplane:
    """The chassis-side mounting plate with the +X hardstop bump.

    Carries a cylindrical relief cut into its top so the tap collar can
    spin freely above it (the v2 plate physically intersected the collar
    OD by 1.5 mm — per PR review v3 we cut a free-running pocket out of
    the plate using the same 0.5 mm diametral fit as the bracket bore).
    """
    plate = cq.Workplane("XY").box(
        PLATE_LENGTH, PLATE_DEPTH, PLATE_THICKNESS, centered=(True, True, False)
    )
    # Hardstop bump on +X, sitting on top of the plate.
    bump_w = BUMP_OUTER_X - BUMP_INNER_X
    bump_centre_x = (BUMP_INNER_X + BUMP_OUTER_X) / 2
    bump = (
        cq.Workplane("XY")
        .workplane(offset=PLATE_THICKNESS)
        .center(bump_centre_x, 0)
        .box(bump_w, BUMP_DEPTH, BUMP_HEIGHT, centered=(True, True, False))
    )
    body = plate.union(bump)

    # Fillet the bump-to-plate intersection on its inboard and outboard
    # Y-parallel base edges so the moment arm at the base is well blended.
    for sx in (BUMP_INNER_X, BUMP_OUTER_X):
        try:
            body = (
                body.edges(
                    cq.selectors.NearestToPointSelector((sx, 0.0, PLATE_THICKNESS))
                ).fillet(FILLET_PLATE_BUMP)
            )
        except Exception:  # pragma: no cover — selector may pick a non-fillet-able edge
            pass

    # Collar relief: cylindrical pocket cut into the plate top, axis along
    # Y, centred on (x=0, z=COLLAR_CENTRE_Z), radius = collar OD/2 + 0.25
    # (= 0.5 mm diametral free-running clearance, matching the bracket
    # bore fit from PR #46 / #47).
    relief_len = PLATE_DEPTH + 2 * COLLAR_RELIEF_DEPTH_OVERSHOOT
    relief = (
        cq.Workplane("XZ")
        .workplane(offset=-relief_len / 2)
        .center(0, COLLAR_CENTRE_Z)
        .circle(COLLAR_RELIEF_R)
        .extrude(relief_len)
    )
    body = body.cut(relief)

    # Corner mounting holes (same pattern as the bracket).  The +X holes
    # punches through the hardstop bump as well — that is intentional, it
    # is the "hollow" cut-out that lets the M3 screw drive through the
    # bump without losing structural width.
    mount_xs = (
        -(PLATE_LENGTH / 2 - MOUNT_HOLE_INSET_X),
        +(PLATE_LENGTH / 2 - MOUNT_HOLE_INSET_X),
    )
    mount_ys = (
        -(PLATE_DEPTH / 2 - MOUNT_HOLE_INSET_Y),
        +(PLATE_DEPTH / 2 - MOUNT_HOLE_INSET_Y),
    )
    for mx in mount_xs:
        for my in mount_ys:
            hole = (
                cq.Workplane("XY")
                .workplane(offset=-1)
                .center(mx, my)
                .circle(MOUNT_HOLE_D / 2)
                .extrude(PLATE_THICKNESS + BUMP_HEIGHT + 2)
            )
            body = body.cut(hole)

    # 90° countersink on the +X mount hole, sunk into the bump top so the
    # screw head sits flush with the bump's top face (PR review v3 —
    # keeps the contact surface flat for the lower clamp tab even with
    # the screw installed).  Built as a cone: Ø MOUNT_HOLE_D at depth
    # CSK_DEPTH below the bump top, Ø CSK_HEAD_D at the bump top.
    csk_x = +(PLATE_LENGTH / 2 - MOUNT_HOLE_INSET_X)
    for csk_y in mount_ys:
        csk = (
            cq.Workplane("XY")
            .workplane(offset=BUMP_TOP_Z - CSK_DEPTH)
            .center(csk_x, csk_y)
            .circle(MOUNT_HOLE_D / 2)
            .workplane(offset=CSK_DEPTH)
            .circle(CSK_HEAD_D / 2)
            .loft(combine=False)
        )
        body = body.cut(csk)

    return body


def _add_coin_motor_pad(body: cq.Workplane) -> cq.Workplane:
    """Rectangular reinforced slab on the -X side with a Ø10 × 1 mm recess.

    The slab sinks PAD_COLLAR_OVERLAP (3 mm) into the collar OD — the
    same reinforcement template the bracket uses for its plate ↔ collar
    intersection — so the slab/cylinder intersection is structurally
    integral instead of a tangent contact line.
    """
    # Mounting face is at X = -(collar_OD/2 + COIN_PAD_PROUD).
    face_x = -(COLLAR_OD / 2 + COIN_PAD_PROUD)
    # Base sinks 3 mm into the collar OD.
    base_x = -(COLLAR_OD / 2 - PAD_COLLAR_OVERLAP)
    pad_thickness = base_x - face_x  # X-thickness of the slab

    slab = (
        cq.Workplane("XY")
        .workplane(offset=COLLAR_CENTRE_Z - COIN_PAD_W / 2)
        .center((face_x + base_x) / 2, 0)
        .box(pad_thickness, COIN_PAD_DEPTH, COIN_PAD_W, centered=(True, True, False))
    )
    body = body.union(slab)

    # Fillet the slab/collar intersection (Y-parallel edges at the top
    # and bottom of the slab where it crosses the cylinder OD) — same
    # cosmetic + stress-relief blend the bracket uses on its plate/collar
    # intersection.
    half_w = COIN_PAD_W / 2
    x_at_z = -math.sqrt(max((COLLAR_OD / 2) ** 2 - half_w ** 2, 0.0))
    for sz in (+half_w, -half_w):
        try:
            body = (
                body.edges(
                    cq.selectors.NearestToPointSelector((x_at_z, 0.0, COLLAR_CENTRE_Z + sz))
                ).fillet(FILLET_PAD_COLLAR)
            )
        except Exception:  # pragma: no cover
            pass

    # Shallow circular recess for the adhesive coin motor, centred on the
    # mounting face.
    recess = (
        cq.Workplane("YZ")
        .workplane(offset=face_x + COIN_MOTOR_RECESS_DEPTH)
        .center(0, COLLAR_CENTRE_Z)
        .circle(COIN_MOTOR_D / 2)
        .extrude(-COIN_MOTOR_RECESS_DEPTH - 0.01)
    )
    body = body.cut(recess)
    return body


def _add_solenoid_boss(body: cq.Workplane) -> cq.Workplane:
    """Rectangular reinforced slab on +Z with the real solenoid mount pattern.

    Same template as the coin pad: a full rectangular slab that sinks
    PAD_COLLAR_OVERLAP (3 mm) into the collar OD, with the
    slab/cylinder intersection filleted for stress relief.  The full
    Y-extent (TC_COLLAR_DEPTH) is solid collar underneath so the mount
    holes sit fully over collar material.

    The two mount holes follow the real Adafruit 412 / TAU0730TM
    flange: diagonally-opposite ears 18.2 mm apart across the body
    and 16.0 mm apart along the body, sized to thread an M3 screw.
    The plunger axis is oriented along X (perpendicular to the auger
    axis) and the tip target is 3 mm into the auger OD at full stroke.
    """
    # Mounting face at Z = COLLAR_TOP_Z + SOLENOID_BOSS_PROUD.
    face_z = COLLAR_TOP_Z + SOLENOID_BOSS_PROUD
    # Base sinks 3 mm into the collar OD from the top.
    base_z = COLLAR_TOP_Z - PAD_COLLAR_OVERLAP
    boss_thickness = face_z - base_z  # Z-thickness of the slab

    slab = (
        cq.Workplane("XY")
        .workplane(offset=base_z)
        .center(0, 0)
        .box(SOLENOID_BOSS_W, SOLENOID_BOSS_DEPTH, boss_thickness, centered=(True, True, False))
    )
    body = body.union(slab)

    # Fillet the slab/collar intersection (Y-parallel edges at the ±X
    # edges of the slab where it crosses the cylinder OD).
    half_w = SOLENOID_BOSS_W / 2
    z_at_x = COLLAR_CENTRE_Z + math.sqrt(max((COLLAR_OD / 2) ** 2 - half_w ** 2, 0.0))
    for sx in (+half_w, -half_w):
        try:
            body = (
                body.edges(
                    cq.selectors.NearestToPointSelector((sx, 0.0, z_at_x))
                ).fillet(FILLET_PAD_COLLAR)
            )
        except Exception:  # pragma: no cover
            pass

    # Mount holes — the real solenoid's two diagonally-opposite M3 flange
    # holes (18.2 mm pitch in X, 16.0 mm in Y).  Driven from the boss top
    # down into the collar wall (~4 mm of thread engagement); both holes
    # sit fully over the lengthened collar.
    for sx, sy in SOLENOID_HOLE_OFFSETS:
        hole = (
            cq.Workplane("XY")
            .workplane(offset=face_z + 1)
            .center(sx, sy)
            .circle(SOLENOID_SCREW_D / 2)
            .extrude(-(SOLENOID_BOSS_PROUD + 4.0))
        )
        body = body.cut(hole)

    # Plunger clearance path — along X (solenoid axis), aimed into the
    # auger.  Target endpoint is 3 mm inside the auger OD.
    plunger_target_x = AUGER_OD / 2 - SOLENOID_INTERFERENCE_INTO_AUGER
    plunger_entry_x = SOLENOID_BOSS_W / 2 + 1.0
    plunger = (
        cq.Workplane("YZ")
        .workplane(offset=plunger_entry_x)
        .center(0, COLLAR_CENTRE_Z)
        .circle(SOLENOID_PLUNGER_D / 2)
        .extrude(-(plunger_entry_x - plunger_target_x))
    )
    body = body.cut(plunger)
    return body


def build_tap_collar() -> cq.Workplane:
    """The split shaft-collar that wraps the auger.

    Geometry mirrors the bracket's collar (bore, OD, slot, clamp ears) but:
      * the slot is rotated 90° so the clamp ears face +X and double as
        the hardstop contact tabs;
      * the collar Y-extent is TC_COLLAR_DEPTH = 24 mm (vs 12 mm on the
        bracket) so the solenoid mounting boss has solid material under
        the full diagonal M3 mount-hole pattern;
      * the coin-motor pad and solenoid boss are rectangular reinforced
        slabs that sink PAD_COLLAR_OVERLAP (3 mm) into the collar OD,
        with the slab/cylinder intersection filleted — same template
        the bracket uses for its plate ↔ collar intersection.
    """
    # Collar cylinder, axis along Y (matching the bracket convention).
    collar = (
        cq.Workplane("XZ")
        .workplane(offset=-TC_COLLAR_DEPTH / 2)
        .center(0, COLLAR_CENTRE_Z)
        .circle(COLLAR_OD / 2)
        .extrude(TC_COLLAR_DEPTH)
    )

    # Clamp tab block on +X.  The block is centered in Z on COLLAR_CENTRE_Z
    # so the two ears straddle the slot symmetrically.
    tabs_total_h = 2 * TC_TAB_H + CLAMP_GAP
    tab_block_x0 = COLLAR_OD / 2 - TAB_COLLAR_OVERLAP  # sink into the OD
    tab_block_w = TAB_COLLAR_OVERLAP + TC_TAB_W
    tabs = (
        cq.Workplane("XY")
        .workplane(offset=COLLAR_CENTRE_Z - tabs_total_h / 2)
        .center(tab_block_x0 + tab_block_w / 2, 0)
        .box(tab_block_w, TC_COLLAR_DEPTH, tabs_total_h, centered=(True, True, False))
    )
    body = collar.union(tabs)

    # Coin-motor pad and solenoid boss are added before the bore / slot
    # cuts so those features punch through any added material as well.
    body = _add_coin_motor_pad(body)
    body = _add_solenoid_boss(body)

    # --- Bore through the collar (auger shaft) -----------------------------
    bore = (
        cq.Workplane("XZ")
        .workplane(offset=-TC_COLLAR_DEPTH / 2 - 1)
        .center(0, COLLAR_CENTRE_Z)
        .circle(BORE_D / 2)
        .extrude(TC_COLLAR_DEPTH + 2)
    )
    body = body.cut(bore)

    # --- Clamp slot: CLAMP_GAP-wide horizontal slot from the bore through
    # the +X collar wall and out past the tab outboard face -----------------
    slot_x0 = 0.0                                           # at bore centre
    slot_x1 = tab_block_x0 + tab_block_w + 1.0              # past tab edge
    slot = (
        cq.Workplane("XY")
        .workplane(offset=COLLAR_CENTRE_Z - CLAMP_GAP / 2)
        .center((slot_x0 + slot_x1) / 2, 0)
        .box(slot_x1 - slot_x0, TC_COLLAR_DEPTH + 2, CLAMP_GAP, centered=(True, True, False))
    )
    body = body.cut(slot)

    # --- Clamp screw hole through both tabs --------------------------------
    # Centred between the inboard face of the tabs (at the collar OD) and
    # the outboard face of the tabs.
    screw_centre_x = (COLLAR_OD / 2 + tab_block_x0 + tab_block_w) / 2
    screw_hole = (
        cq.Workplane("XY")
        .workplane(offset=COLLAR_CENTRE_Z + CLAMP_GAP / 2 + TC_TAB_H + 1)
        .center(screw_centre_x, 0)
        .circle(CLAMP_SCREW_D / 2)
        .extrude(-(2 * TC_TAB_H + CLAMP_GAP + 2))
    )
    body = body.cut(screw_hole)

    # --- Smooth tab/collar transition (cosmetic + stress relief) -----------
    # Edges to fillet are the Y-parallel intersection edges where the tab
    # block meets the cylinder OD, at the top and bottom of the tab block.
    half_th = tabs_total_h / 2
    x_at_z = math.sqrt(max((COLLAR_OD / 2) ** 2 - half_th ** 2, 0.0))
    for sz in (+half_th, -half_th):
        try:
            body = (
                body.edges(
                    cq.selectors.NearestToPointSelector((+x_at_z, 0.0, COLLAR_CENTRE_Z + sz))
                ).fillet(FILLET_TAB_COLLAR)
            )
        except Exception:  # pragma: no cover
            pass

    return body


def export(out_dir: Path | None = None) -> dict[str, Path]:
    """Export STEP + per-part STLs.  Returns the paths for the caller."""
    out_dir = out_dir or Path(__file__).parent
    stl_dir = out_dir / "stl"
    stl_dir.mkdir(parents=True, exist_ok=True)

    parts = {
        "mount_plate": build_mount_plate(),
        "tap_collar": build_tap_collar(),
    }
    written: dict[str, Path] = {}
    for name, body in parts.items():
        step_path = out_dir / f"{name}.step"
        stl_path = stl_dir / f"{name}.stl"
        cq.exporters.export(body, str(step_path))
        cq.exporters.export(body, str(stl_path), tolerance=0.05, angularTolerance=0.2)
        written[f"{name}.step"] = step_path
        written[f"{name}.stl"] = stl_path
    return written


if __name__ == "__main__":
    paths = export()
    for kind, p in paths.items():
        print(f"wrote {kind}: {p}")
