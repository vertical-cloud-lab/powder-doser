"""Parametric auger bracket (split shaft-collar) for the Powder Doser.

Implements the bracket sketched in the issue "Part-by-part Powder Doser
Approach": a small split-collar bracket that grips the auger shaft on top of
a rectangular mounting plate. A single screw at the top tightens the two
collar halves around the auger, while the plate is screwed down to the
chassis. The collar/plate intersection is filleted so it is not a stress
riser.

Print orientation: plate face down on the bed (the face called out as
"print on this face" in the drawing). This keeps the bore axis horizontal
and avoids supports inside the collar.

Run from the package directory to (re)generate the STEP + STL exports::

    cd design/cad/auger-bracket
    python cad_model.py
"""

from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq

# ---------------------------------------------------------------------------
# Parameters (mm)
# ---------------------------------------------------------------------------
# Auger shaft and bore.  Sized to PR #16 (Archimedes auger): outer_diameter
# = 25 mm, total_height = 250 mm, M3 spindle mount on top.  A diametral
# clearance of 0.5 mm gives a comfortable running fit on an FDM print
# (accounts for elephant-foot / first-layer squish on the bore walls) while
# still keeping the shaft well constrained.
AUGER_OD = 25.0
BORE_CLEARANCE = 0.5  # diametral clearance for a free-running fit
BORE_D = AUGER_OD + BORE_CLEARANCE  # = 25.5 mm

# Collar wall thickness and resulting collar OD.
COLLAR_WALL = 4.0
COLLAR_OD = BORE_D + 2 * COLLAR_WALL  # = 33.5 mm

# Plate (mounting flange) — "print on this face" is the bottom of this plate.
# Sized so the collar OD (33.5 mm) fits with comfortable margin to each
# corner mounting hole.
#
# PR review (williamulbz, post-#49 follow-up): with the geared auger from
# PR #49 the gear OD reaches Ø50 mm (gear_tip_r = 25 mm, auger OR = 12.5 mm
# → 12.5 mm radial protrusion past the bare-shaft surface), so when the
# bracket is mounted on the chassis baseplate the auger axis must sit
# higher than 25 mm above the plate bottom or the gear teeth will collide
# with the baseplate as the auger rotates.  PLATE_THICKNESS was 4 mm,
# putting the bore axis at COLLAR_CENTRE_Z = 4 + 16.75 - 1.5 = 19.25 mm
# (≈5.75 mm of interference with the gear).  Bumped to 14 mm → bore axis
# at 29.25 mm → 4.25 mm radial clearance between the gear OD and the
# baseplate.  All collar / tab / fillet / clamp-screw geometry is keyed to
# COLLAR_CENTRE_Z / COLLAR_TOP_Z, so it auto-translates with the lift, and
# the corner mounting holes still pass straight through to the bottom face.
PLATE_LENGTH = 60.0    # X — long axis, with mounting holes near each end
PLATE_DEPTH = 12.0     # Y — bore length along the auger axis
PLATE_THICKNESS = 14.0  # Z — total plate height; ≥9 mm of "lift" added to
                       # the original 4 mm so the geared auger (gear tip
                       # radius 25 mm, PR #49) clears the chassis baseplate

# Top clamp tabs (the two ears separated by the 2 mm gap on top).
#
# PR review (williamulbz, follow-up): the tabs don't need to be thick *along
# the screw axis* — the M3 tightening screw is along X, perpendicular to the
# auger and parallel to the bottom mounting face, so a smaller TOP_TAB_W
# means a shorter screw that goes through less material.  At the same time,
# TOP_TAB_H must be large enough that the screw hole (Ø CLAMP_SCREW_D) sits
# centred between the top of the collar circle and the top of the part with
# real material above and below it.
TOP_GAP = 2.0          # called out as "2 mm" on the drawing
TOP_TAB_W = 3.0        # X-width of each ear (= half the screw length per
                       # ear, kept slim so the M3 is short — review feedback)
TOP_TAB_H = 7.0        # Z-height above the collar OD: ~1.8 mm wall above
                       # and below the centred Ø3.4 hole (CLAMP_SCREW_D)
CLAMP_SCREW_D = 3.4    # M3 clearance hole through both tabs

# How far the tab block sinks into the collar so the union forms a continuous
# solid (not a knife-edge tangent).  Sized so the tab's outer X-faces
# (X = ±half_tab_width) actually penetrate the cylinder OD by ~1 mm at the
# tab base elevation, giving the FILLET_TAB_COLLAR blend room to work and
# making the ears appear to grow out of the collar wall rather than sit on
# top of it.  See PR review feedback (#34 follow-up).
TAB_COLLAR_OVERLAP = 6.0

# Mounting holes through the plate (one near each corner).
MOUNT_HOLE_D = 3.4     # M3 clearance
MOUNT_HOLE_INSET_X = 6.0  # distance from each plate end (X) to hole centre
# Mounting holes are centred in Y (plate depth = 12 mm, hole D = 3.4 mm).

# Fillets.  The collar/plate intersection is the callout "smooth transition"
# from the drawing — make it generous so the moment arm at the base is well
# blended.  The tab/collar intersection gets the same treatment per PR
# review feedback (so the clamp ears are integrally joined to the collar
# body, not just sitting on top).
FILLET_COLLAR_PLATE = 3.0
FILLET_TAB_COLLAR = 1.0
FILLET_TAB_TOP = 1.0

# How far the collar dips into the plate top before fillet blending.  Picked
# so that FILLET_COLLAR_PLATE (3 mm) has clean geometry to bite into without
# eating through the plate (PLATE_THICKNESS = 4 mm).
COLLAR_PLATE_OVERLAP = 1.5

# ---------------------------------------------------------------------------
# Derived geometry
# ---------------------------------------------------------------------------
# Place the collar so a small portion overlaps the plate.  The overlap is
# what the FILLET_COLLAR_PLATE fillet will smooth into a tangent blend.
COLLAR_CENTRE_Z = PLATE_THICKNESS + COLLAR_OD / 2 - COLLAR_PLATE_OVERLAP
COLLAR_TOP_Z = COLLAR_CENTRE_Z + COLLAR_OD / 2

# Constraint: the tab block's outer X-faces must lie within the collar OD
# at Y = 0 (i.e. the half-tab-width must not exceed the collar radius), so
# the tab/collar union has a real intersection edge that
# FILLET_TAB_COLLAR can blend.  Catch parameter retunes that violate this.
assert (2 * TOP_TAB_W + TOP_GAP) / 2 <= COLLAR_OD / 2, (
    "Tab footprint wider than collar OD: "
    f"half_tw={(2 * TOP_TAB_W + TOP_GAP) / 2} > collar_r={COLLAR_OD / 2}"
)


def _apply_features(body: cq.Workplane) -> cq.Workplane:
    """Apply fillets and subtractive features (bore, slot, screw holes)."""

    # --- Smooth collar/plate transition ---------------------------------
    # The plate-top face and the collar OD intersect in two edges (Y-parallel
    # lines when the collar OD extends beyond the plate top, or arcs when it
    # doesn't quite reach).  Compute the true X of the intersection at
    # Y = 0, Z = PLATE_THICKNESS so the selector finds the right edge across
    # any reasonable AUGER_OD / COLLAR_WALL retune.
    dz = COLLAR_CENTRE_Z - PLATE_THICKNESS
    tp_x = math.sqrt(max((COLLAR_OD / 2) ** 2 - dz ** 2, 0.0))
    tp_y = 0.0
    tp_z = PLATE_THICKNESS
    body = (
        body.edges(cq.selectors.NearestToPointSelector((+tp_x, tp_y, tp_z)))
        .fillet(FILLET_COLLAR_PLATE)
    )
    body = (
        body.edges(cq.selectors.NearestToPointSelector((-tp_x, tp_y, tp_z)))
        .fillet(FILLET_COLLAR_PLATE)
    )

    # --- Smooth tab/collar transition (PR review: tabs must be integrally
    # joined to the collar body, not just sit on top).  Sinking the tab
    # block into the collar via TAB_COLLAR_OVERLAP already provides the
    # structural merge; the fillet below is the cosmetic / stress-relieving
    # blend on the resulting Y-parallel intersection edges.
    half_tw = (2 * TOP_TAB_W + TOP_GAP) / 2
    z_above_centre = math.sqrt(max((COLLAR_OD / 2) ** 2 - half_tw ** 2, 0.0))
    tab_int_z = COLLAR_CENTRE_Z + z_above_centre
    tab_int_y = 0.0
    for sx in (+half_tw, -half_tw):
        try:
            body = (
                body.edges(
                    cq.selectors.NearestToPointSelector((sx, tab_int_y, tab_int_z))
                ).fillet(FILLET_TAB_COLLAR)
            )
        except Exception:  # pragma: no cover — selector may pick a non-fillet-able edge
            pass

    # --- Bore through the collar (auger shaft), absolute coords ---------
    bore = (
        cq.Workplane("XZ")
        .workplane(offset=-PLATE_DEPTH / 2 - 1)
        .center(0, COLLAR_CENTRE_Z)
        .circle(BORE_D / 2)
        .extrude(PLATE_DEPTH + 2)
    )
    body = body.cut(bore)

    # --- Clamp slot: 2 mm vertical slot from bore through to the top of
    # the tabs, centred on X = 0.  This is what splits the collar into two
    # halves so the screw can pinch them together.
    slot_bottom_z = COLLAR_CENTRE_Z  # start at the bore centre level
    slot_top_z = COLLAR_TOP_Z + TOP_TAB_H + 1.0  # break through the top
    slot = (
        cq.Workplane("XY")
        .workplane(offset=slot_bottom_z)
        .box(
            TOP_GAP,
            PLATE_DEPTH + 2,
            slot_top_z - slot_bottom_z,
            centered=(True, True, False),
        )
    )
    body = body.cut(slot)

    # --- Clamp screw hole through both tabs -----------------------------
    # Centred between the top of the collar circle (Z = COLLAR_TOP_Z) and
    # the top of the part (Z = COLLAR_TOP_Z + TOP_TAB_H), per PR review.
    screw_centre_z = COLLAR_TOP_Z + TOP_TAB_H / 2
    screw_hole = (
        cq.Workplane("YZ")
        .workplane(offset=-(TOP_TAB_W + TOP_GAP / 2 + 1))
        .center(0, screw_centre_z)
        .circle(CLAMP_SCREW_D / 2)
        .extrude(2 * TOP_TAB_W + TOP_GAP + 2)
    )
    body = body.cut(screw_hole)

    # --- Plate mounting holes (one near each corner) --------------------
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

    # --- Cosmetic break on the top corners of the tabs ------------------
    try:
        body = body.edges(">Z").fillet(FILLET_TAB_TOP)
    except Exception:  # pragma: no cover — selector may pick nothing
        pass

    return body


def build() -> cq.Workplane:
    """Top-level builder used by the script and the renderer."""
    # Start fresh — build_bracket() does the additive part and immediately
    # delegates to build_bracket_finalize().  We replace the helper-style
    # entry point with a direct call here for clarity.
    plate = cq.Workplane("XY").box(
        PLATE_LENGTH, PLATE_DEPTH, PLATE_THICKNESS, centered=(True, True, False)
    )
    collar = (
        cq.Workplane("XZ")
        .workplane(offset=-PLATE_DEPTH / 2)
        .center(0, COLLAR_CENTRE_Z)
        .circle(COLLAR_OD / 2)
        .extrude(PLATE_DEPTH)
    )
    tabs_total_w = 2 * TOP_TAB_W + TOP_GAP
    # Sink the tab block into the collar by TAB_COLLAR_OVERLAP so the union
    # produces a real merged solid with a fillet-able intersection (rather
    # than the previous knife-edge tangent at the top of the cylinder).
    tabs_z0 = COLLAR_TOP_Z - TAB_COLLAR_OVERLAP
    tabs_height = TAB_COLLAR_OVERLAP + TOP_TAB_H
    tabs = (
        cq.Workplane("XY")
        .workplane(offset=tabs_z0)
        .box(tabs_total_w, PLATE_DEPTH, tabs_height, centered=(True, True, False))
    )
    body = plate.union(collar).union(tabs)
    return _apply_features(body)


def export(out_dir: Path | None = None) -> dict[str, Path]:
    """Export STEP + STL.  Returns the paths for the caller to log."""
    out_dir = out_dir or Path(__file__).parent
    stl_dir = out_dir / "stl"
    stl_dir.mkdir(parents=True, exist_ok=True)

    body = build()

    step_path = out_dir / "auger_bracket.step"
    stl_path = stl_dir / "auger_bracket.stl"

    cq.exporters.export(body, str(step_path))
    cq.exporters.export(body, str(stl_path), tolerance=0.05, angularTolerance=0.2)

    return {"step": step_path, "stl": stl_path}


if __name__ == "__main__":
    paths = export()
    for kind, p in paths.items():
        print(f"wrote {kind}: {p}")
