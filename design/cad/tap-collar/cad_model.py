"""Parametric tap-collar assembly for the Powder Doser auger.

The tap collar is the third printed part in the part-by-part Powder Doser
build (after the auger of PR #16 and the auger bracket of PR #47).  It is
made of two independent printed pieces that are not rigidly attached to
each other or to the chassis baseplate:

* **Mounting plate** — a rectangular flange that bolts to the chassis with
  four corner M3 screws (same footprint and corner-hole pattern as the
  auger bracket), but instead of a circular collar it has a *raised
  hardstop column* sticking up off the +X end of the top face.
* **Tap collar** — a split shaft-collar (same bore / OD / clamp-slot /
  clamp-ear geometry as the auger bracket) that wraps around the auger
  with a free-running fit.  The clamp slot is rotated 90° from the
  bracket so the slot opens to the +X side and the two clamp ears form a
  pair of "contact-point" tabs that hit the mounting-plate column to
  arrest rotation.  The collar also carries:

    - a flat *side pad* on the -X side for adhesive-mounting a Ø10 mm
      coin vibration motor, and
    - a flat *top boss* on the +Z side with two M2 mounting holes for a
      small push/pull solenoid plus a plunger-clearance hole through the
      collar wall so the solenoid plunger can tap the auger directly.

The collar is meant to spin freely on the auger (the clamp screw lets you
adjust the running fit but is not torqued down), while the column on the
mounting plate keeps the collar from being dragged around with the auger
and winding up the motor / solenoid wiring.

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
PLATE_DEPTH = 12.0               # Y (along the auger axis)
PLATE_THICKNESS = 14.0           # Z (lifted to clear the PR #49 gear OD)

MOUNT_HOLE_D = 3.4               # M3 clearance through-hole
MOUNT_HOLE_INSET_X = 6.0         # from each plate end (X) to hole centre

# Bore-axis Z above the plate bottom — kept identical to the bracket so the
# tap collar sits at the same height on the chassis as the brackets.
COLLAR_PLATE_OVERLAP = 1.5
COLLAR_CENTRE_Z = PLATE_THICKNESS + COLLAR_OD / 2 - COLLAR_PLATE_OVERLAP
COLLAR_TOP_Z = COLLAR_CENTRE_Z + COLLAR_OD / 2

# Top clamp tabs (the two ears separated by the clamp slot).  Same Z height
# and clamp-screw centring rule as the bracket; tabs are widened along the
# slot-open direction (here X) so they double as the hardstop "contact
# point" reaching out to the mounting-plate column.
CLAMP_GAP = 2.0                  # clamp slot width (drawing callout)
CLAMP_SCREW_D = 3.4              # M3 clearance through both tabs

# Bracket TOP_TAB_W is 3 mm; here we widen the tabs along their projection
# axis to TC_TAB_W = 8 mm so they reach the +X hardstop column without
# needing a separate "stop arm" feature.  TC_TAB_H matches the bracket so
# the M3 clamp screw hole still has ~1.8 mm of wall above and below it.
TC_TAB_W = 8.0                   # tab length along the slot-open direction
TC_TAB_H = 7.0                   # tab thickness perpendicular to the slot
TAB_COLLAR_OVERLAP = 6.0         # how far the tab block sinks into the collar

# Fillets — same recipe as the bracket.
FILLET_TAB_COLLAR = 1.0
FILLET_TAB_TOP = 1.0
FILLET_PLATE_COLUMN = 2.0

# ---------------------------------------------------------------------------
# Mounting-plate-only parameters
# ---------------------------------------------------------------------------
# Hardstop column rising off the +X end of the mounting plate.  Sized so
# that:
#   * the inboard column face sits just outboard of the resting clamp-tab
#     outboard face (plus a small running-clearance angle), and
#   * the outboard column face stays clear of the +X corner mount holes
#     so the M3 screwdriver still has access.
TC_TAB_OUTBOARD_X = CLAMP_GAP / 2 + TC_TAB_W   # = 9.0 mm
COLUMN_GAP = 1.0                 # rotational clearance at rest
COLUMN_INNER_X = TC_TAB_OUTBOARD_X + COLUMN_GAP  # = 10.0 mm
COLUMN_W = 6.0                   # X-thickness of the column
COLUMN_OUTER_X = COLUMN_INNER_X + COLUMN_W       # = 16.0 mm
# Mount hole centre at X = PLATE_LENGTH/2 - MOUNT_HOLE_INSET_X = 24 mm,
# so its inboard edge sits at X = 24 - 1.7 = 22.3 mm; column outboard
# face at 16 mm leaves 6.3 mm of clear access for the screw head.
assert COLUMN_OUTER_X < (PLATE_LENGTH / 2 - MOUNT_HOLE_INSET_X) - MOUNT_HOLE_D / 2 - 2.0, (
    "Hardstop column would foul the +X corner mount holes; "
    "shrink COLUMN_W or move it inboard."
)
COLUMN_DEPTH = PLATE_DEPTH       # Y — full plate depth so it presents a
                                 # 12 mm contact face to the clamp tabs
# Column tall enough to overlap the full clamp-tab Z range with margin.
COLUMN_TOP_Z = COLLAR_TOP_Z + TC_TAB_H + 1.0
COLUMN_HEIGHT = COLUMN_TOP_Z - PLATE_THICKNESS

# ---------------------------------------------------------------------------
# Tap-collar-only parameters: coin-motor side pad and solenoid top boss
# ---------------------------------------------------------------------------
# Coin vibration motor (e.g. 10 mm Ø × 3 mm thick adhesive coin motor).
# A flat tangent pad on the -X side of the collar with a shallow circular
# recess locates the motor for adhesive mounting.
COIN_MOTOR_D = 10.0
COIN_MOTOR_RECESS_DEPTH = 1.0
COIN_PAD_W = 14.0                # Z-extent of the flat pad
COIN_PAD_DEPTH = PLATE_DEPTH     # Y-extent (matches collar/plate depth)
COIN_PAD_PROUD = 1.0             # how far the flat face sits outboard of
                                 # the collar OD's tangent at -X

# Push/pull solenoid (small, e.g. ~17 × 11 × 30 mm with M2 screw holes
# 12 mm apart on its mounting face).  We expose a flat boss on +Z with two
# M2 clearance holes and a Ø6 plunger-clearance through the collar wall.
SOLENOID_BOSS_W = 14.0           # X-extent of the top boss
SOLENOID_BOSS_DEPTH = 17.0       # Y-extent (wider than plate depth so the
                                 # M2 mount holes can straddle the plunger
                                 # hole with clear material between them)
SOLENOID_BOSS_PROUD = 2.0        # how far the boss sits proud of COLLAR_TOP_Z
SOLENOID_SCREW_D = 2.4           # M2 clearance
SOLENOID_SCREW_PITCH_Y = 12.0    # M2 holes spacing along Y (auger axis)
SOLENOID_PLUNGER_D = 6.0         # plunger clearance hole through the wall
# Sanity check: M2 mount holes must clear the central plunger hole.
assert SOLENOID_SCREW_PITCH_Y / 2 - SOLENOID_SCREW_D / 2 > SOLENOID_PLUNGER_D / 2 + 0.5, (
    "Solenoid M2 mount holes overlap the plunger clearance hole."
)
# Sanity check: M2 mount holes must stay inside the boss footprint with
# at least 1 mm of edge wall.
assert SOLENOID_SCREW_PITCH_Y / 2 + SOLENOID_SCREW_D / 2 + 1.0 <= SOLENOID_BOSS_DEPTH / 2, (
    "Solenoid M2 mount holes fall outside the boss footprint."
)

# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------
def build_mount_plate() -> cq.Workplane:
    """The chassis-side mounting plate with the hardstop column."""
    plate = cq.Workplane("XY").box(
        PLATE_LENGTH, PLATE_DEPTH, PLATE_THICKNESS, centered=(True, True, False)
    )
    # Hardstop column on +X.
    col_centre_x = (COLUMN_INNER_X + COLUMN_OUTER_X) / 2
    column = (
        cq.Workplane("XY")
        .workplane(offset=PLATE_THICKNESS)
        .center(col_centre_x, 0)
        .box(COLUMN_W, COLUMN_DEPTH, COLUMN_HEIGHT, centered=(True, True, False))
    )
    body = plate.union(column)

    # Fillet the column-to-plate intersection on its inboard and outboard
    # Y-parallel base edges so the moment arm at the base is well blended.
    for sx in (COLUMN_INNER_X, COLUMN_OUTER_X):
        try:
            body = (
                body.edges(
                    cq.selectors.NearestToPointSelector((sx, 0.0, PLATE_THICKNESS))
                ).fillet(FILLET_PLATE_COLUMN)
            )
        except Exception:  # pragma: no cover — selector may pick a non-fillet-able edge
            pass

    # Corner mounting holes (same pattern as the bracket).
    mount_xs = (
        -(PLATE_LENGTH / 2 - MOUNT_HOLE_INSET_X),
        +(PLATE_LENGTH / 2 - MOUNT_HOLE_INSET_X),
    )
    for mx in mount_xs:
        hole = (
            cq.Workplane("XY")
            .workplane(offset=-1)
            .center(mx, 0)
            .circle(MOUNT_HOLE_D / 2)
            .extrude(PLATE_THICKNESS + 2)
        )
        body = body.cut(hole)

    return body


def _add_coin_motor_pad(body: cq.Workplane) -> cq.Workplane:
    """Flat tangent pad with a Ø10 × 1 mm adhesive recess on the -X side."""
    pad_outer_x = -(COLLAR_OD / 2 + COIN_PAD_PROUD)
    pad_inner_x = -(COLLAR_OD / 2 - 0.5)  # bury 0.5 mm into the collar wall
    pad_w_x = pad_inner_x - pad_outer_x
    pad_centre_x = (pad_outer_x + pad_inner_x) / 2
    pad = (
        cq.Workplane("XY")
        .workplane(offset=COLLAR_CENTRE_Z - COIN_PAD_W / 2)
        .center(pad_centre_x, 0)
        .box(pad_w_x, COIN_PAD_DEPTH, COIN_PAD_W, centered=(True, True, False))
    )
    body = body.union(pad)
    # Shallow circular recess for the adhesive coin motor.
    recess = (
        cq.Workplane("YZ")
        .workplane(offset=pad_outer_x + COIN_MOTOR_RECESS_DEPTH)
        .center(0, COLLAR_CENTRE_Z)
        .circle(COIN_MOTOR_D / 2)
        .extrude(-COIN_MOTOR_RECESS_DEPTH - 0.01)
    )
    body = body.cut(recess)
    return body


def _add_solenoid_boss(body: cq.Workplane) -> cq.Workplane:
    """Flat boss on top with two M2 mounting holes + a Ø6 plunger hole."""
    boss = (
        cq.Workplane("XY")
        .workplane(offset=COLLAR_TOP_Z - 0.5)  # bury 0.5 mm into the OD
        .center(0, 0)
        .box(
            SOLENOID_BOSS_W,
            SOLENOID_BOSS_DEPTH,
            SOLENOID_BOSS_PROUD + 0.5,
            centered=(True, True, False),
        )
    )
    body = body.union(boss)

    boss_top_z = COLLAR_TOP_Z - 0.5 + SOLENOID_BOSS_PROUD + 0.5
    # M2 mounting holes — through the boss but stop above the bore.
    for sy in (-SOLENOID_SCREW_PITCH_Y / 2, +SOLENOID_SCREW_PITCH_Y / 2):
        hole = (
            cq.Workplane("XY")
            .workplane(offset=boss_top_z + 1)
            .center(0, sy)
            .circle(SOLENOID_SCREW_D / 2)
            .extrude(-(SOLENOID_BOSS_PROUD + 4.0))  # ~4 mm of thread engagement
        )
        body = body.cut(hole)

    # Plunger clearance hole — straight down from the boss top through the
    # full collar wall so the solenoid plunger can reach the auger surface.
    plunger = (
        cq.Workplane("XY")
        .workplane(offset=boss_top_z + 1)
        .center(0, 0)
        .circle(SOLENOID_PLUNGER_D / 2)
        .extrude(-(boss_top_z + 1 - COLLAR_CENTRE_Z))
    )
    body = body.cut(plunger)
    return body


def build_tap_collar() -> cq.Workplane:
    """The split shaft-collar that wraps the auger.

    Geometry mirrors the bracket's collar (bore, OD, slot, clamp ears) but
    the slot is rotated 90° so the clamp ears face +X and double as the
    hardstop contact tabs.  Adds a coin-motor side pad and a solenoid top
    boss.
    """
    # Collar cylinder, axis along Y (matching the bracket convention).
    collar = (
        cq.Workplane("XZ")
        .workplane(offset=-PLATE_DEPTH / 2)
        .center(0, COLLAR_CENTRE_Z)
        .circle(COLLAR_OD / 2)
        .extrude(PLATE_DEPTH)
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
        .box(tab_block_w, PLATE_DEPTH, tabs_total_h, centered=(True, True, False))
    )
    body = collar.union(tabs)

    # Coin-motor pad and solenoid boss are added before the bore / slot
    # cuts so those features punch through any added material as well.
    body = _add_coin_motor_pad(body)
    body = _add_solenoid_boss(body)

    # --- Bore through the collar (auger shaft) -----------------------------
    bore = (
        cq.Workplane("XZ")
        .workplane(offset=-PLATE_DEPTH / 2 - 1)
        .center(0, COLLAR_CENTRE_Z)
        .circle(BORE_D / 2)
        .extrude(PLATE_DEPTH + 2)
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
        .box(slot_x1 - slot_x0, PLATE_DEPTH + 2, CLAMP_GAP, centered=(True, True, False))
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
