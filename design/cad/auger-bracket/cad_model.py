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

from pathlib import Path

import cadquery as cq

# ---------------------------------------------------------------------------
# Parameters (mm)
# ---------------------------------------------------------------------------
# Auger shaft and bore.  Auger OD is taken as a typical small auger (8 mm).
# A diametral clearance of 0.5 mm gives a comfortable running fit on an FDM
# print (accounts for elephant-foot / first-layer squish on the bore walls)
# while still keeping the shaft well constrained.
AUGER_OD = 8.0
BORE_CLEARANCE = 0.5  # diametral clearance for a free-running fit
BORE_D = AUGER_OD + BORE_CLEARANCE

# Collar wall thickness and resulting collar OD.
COLLAR_WALL = 4.0
COLLAR_OD = BORE_D + 2 * COLLAR_WALL  # = 16.5 mm

# Plate (mounting flange) — "print on this face" is the bottom of this plate.
PLATE_LENGTH = 40.0   # X — long axis, with mounting holes near each end
PLATE_DEPTH = 10.0    # Y — into the page in the iso view, matches "10 mm"
PLATE_THICKNESS = 4.0  # Z

# Top clamp tabs (the two ears separated by the 2 mm gap on top).
TOP_GAP = 2.0          # called out as "2 mm" on the drawing
TOP_TAB_W = 6.0        # X-width of each ear
TOP_TAB_H = 6.0        # Z-height of each ear above the collar OD
CLAMP_SCREW_D = 3.4    # M3 clearance hole through both tabs

# Mounting holes through the plate (one near each corner).
MOUNT_HOLE_D = 3.4     # M3 clearance
MOUNT_HOLE_INSET_X = 5.0  # distance from each plate end (X) to hole centre
# Mounting holes are centred in Y (plate depth = 10 mm, hole D = 3.4 mm).

# Fillets.  The collar/plate intersection is the callout "smooth transition"
# from the drawing — make it generous so the moment arm at the base is well
# blended.  The top tab corners get a smaller cosmetic break.
FILLET_COLLAR_PLATE = 3.0
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


def _apply_features(body: cq.Workplane) -> cq.Workplane:
    """Apply fillets and subtractive features (bore, slot, screw holes)."""

    # --- Smooth collar/plate transition ---------------------------------
    # The plate-top face and the collar OD intersect along two arcs that
    # become straight edges in Y after the cylindrical/planar boolean.  Pick
    # them by proximity to the two tangent points.
    tp_y = 0.0  # any Y on the edge works for selection
    tp_x = COLLAR_OD / 2 * 0.95  # slightly inside the collar OD
    tp_z = PLATE_THICKNESS
    body = (
        body.edges(cq.selectors.NearestToPointSelector((+tp_x, tp_y, tp_z)))
        .fillet(FILLET_COLLAR_PLATE)
    )
    body = (
        body.edges(cq.selectors.NearestToPointSelector((-tp_x, tp_y, tp_z)))
        .fillet(FILLET_COLLAR_PLATE)
    )

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
    screw_hole = (
        cq.Workplane("YZ")
        .workplane(offset=-(TOP_TAB_W + TOP_GAP / 2 + 1))
        .center(0, COLLAR_TOP_Z + TOP_TAB_H / 2)
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
    tabs = (
        cq.Workplane("XY")
        .workplane(offset=COLLAR_TOP_Z)
        .box(tabs_total_w, PLATE_DEPTH, TOP_TAB_H, centered=(True, True, False))
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
