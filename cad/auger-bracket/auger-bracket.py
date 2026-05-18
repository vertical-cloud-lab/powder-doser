"""
Powder Excavator — Auger Bracket  (split shaft collar + mounting flange)
========================================================================

Companion to the Archimedes auger from PR #16
(``cad/auger/archimedes-auger.scad`` — ``outer_diameter = 25 mm``,
``total_height = 250 mm``).  Two of these brackets support the auger
near its ends, leaving the centre span clear for the planned solenoid
(#25) and coin-vibration motor (#31).

Design intent (per the hand sketch in the source issue):

    * Shaft-collar ring that wraps the auger with a small slip-fit
      clearance.
    * A 2 mm-wide vertical slit cuts the ring + ears in two so a
      single M3 clamp screw across the ears pinches the ring tight
      onto the auger after installation.
    * Mounting flange under the ring, ~10 mm thick, with a smooth
      fillet between the ring and the flange ("smooth transition"
      callout in the sketch).
    * Two M3 mounting holes through the flange so the bracket can be
      screwed down to the frame ("Print on this face" = flange-down
      face, no supports needed).

Reproduce
---------

::

    pip install cadquery               # cadquery==2.7.0
    python3 cad/auger-bracket/auger-bracket.py

writes::

    cad/auger-bracket/auger-bracket.step
    cad/auger-bracket/auger-bracket.stl

A second helper renders four views of the part and a third stages it
against the PR #16 auger; see ``render_views.py`` and
``render_assembly.py``.
"""

from __future__ import annotations

from pathlib import Path

import cadquery as cq


# --------------------------------------------------------------------- #
# Parameters — all in millimetres
# --------------------------------------------------------------------- #
# Matches outer_diameter in cad/auger/archimedes-auger.scad (PR #16).
AUGER_OD = 25.0

# 0.4 mm diametral clearance (~0.2 mm per side) for an FDM slip-fit.
# After clamping, the 2 mm slit closes a bit and the ring grips the
# auger surface — a standard shaft-collar arrangement.
BORE_CLEARANCE_D = 0.4
BORE_D = AUGER_OD + BORE_CLEARANCE_D       # 25.4 mm
BORE_R = BORE_D / 2.0                      # 12.70 mm

# Ring wall: 5 mm radial — plenty of meat for the M3 clamp screw to
# pull through without cracking PLA/PETG.
RING_WALL = 5.0
RING_OR = BORE_R + RING_WALL               # 17.70 mm
RING_OD = RING_OR * 2.0                    # 35.40 mm

# Axial width of the collar (along the auger axis).
RING_WIDTH = 15.0

# 2 mm clamping slit (the "2mm" callout in the sketch) — cuts straight
# down through both ears and through the top of the ring to the bore,
# so tightening the clamp screw squeezes the ring closed.
SLIT_WIDTH = 2.0

# Clamp ears (sit on top of the ring).
EAR_WIDTH = 8.0          # ear footprint along the auger axis (matches ring width region)
EAR_THICK = 8.0          # ear thickness in the squeeze direction (per side of slit)
EAR_HEIGHT = 10.0        # how far the ears project above the ring OD

# M3 clamp screw across the ears (Ø3.2 mm clearance, both ears thru).
M3_CLEARANCE_D = 3.2
CLAMP_HOLE_Z_FROM_RING_TOP = EAR_HEIGHT / 2.0   # centred vertically in the ears

# Mounting flange (the "Print on this face" face).
FLANGE_W = 60.0          # left/right (perpendicular to the auger axis)
FLANGE_D = 25.0          # front/back (along the auger axis = RING_WIDTH + a touch)
FLANGE_T = 10.0          # thickness — the "10 mm" callout
FLANGE_FILLET = 2.0      # smooth transition from flange into the ring

# Two M3 mounting holes through the flange corners.
MOUNT_HOLE_INSET_X = 6.0     # inset from the flange end in the squeeze direction
MOUNT_HOLE_INSET_Y = FLANGE_D / 2.0          # centred along auger axis (one hole each side)
MOUNT_COUNTERBORE_D = 6.0
MOUNT_COUNTERBORE_DEPTH = 3.0


# --------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------- #
# Coordinate convention:
#   * The auger axis runs along +Y (so the bracket "wraps" around Y).
#   * +Z is up (clamp ears point up, flange face sits on z = 0).
#   * +X is the squeeze direction (the 2 mm slit lies in the Y-Z plane
#     at x = 0).
#
# This makes the "print on this face" face the z = 0 face of the
# flange, which is the build-plate face.

# Z of the ring centre above the flange top: leave a little clearance
# so the fillet has room to grow.
RING_CENTRE_Z = FLANGE_T + RING_OR * 0.55     # ring sits up off the flange
RING_TOP_Z = RING_CENTRE_Z + RING_OR

# Flange — a simple block on the XY plane, fillet the top edges that
# meet the ring later.
flange = (
    cq.Workplane("XY")
    .box(FLANGE_W, FLANGE_D, FLANGE_T, centered=(True, True, False))
)

# Mounting holes through the flange (counterbored for an M3 cap screw).
flange = (
    flange.faces(">Z").workplane(origin=(0, 0, FLANGE_T))
    .pushPoints([
        (+FLANGE_W / 2.0 - MOUNT_HOLE_INSET_X, 0),
        (-FLANGE_W / 2.0 + MOUNT_HOLE_INSET_X, 0),
    ])
    .cboreHole(
        diameter=M3_CLEARANCE_D,
        cboreDiameter=MOUNT_COUNTERBORE_D,
        cboreDepth=MOUNT_COUNTERBORE_DEPTH,
    )
)

# Collar — a solid annulus along Y (bore subtracted up front so it
# cannot eat into the flange / pillar below the ring).
collar = (
    cq.Workplane("XZ")
    .workplane(offset=-RING_WIDTH / 2.0)
    .center(0, RING_CENTRE_Z)
    .circle(RING_OR)
    .circle(BORE_R)
    .extrude(RING_WIDTH)
)
# Cylindrical channel for the bore through the pillar too, but only
# the upper hemisphere of the bore — i.e. cut a half-cylinder out of
# the pillar so the auger can slide in through the top and clear the
# pillar shoulders.  Stops at the ring centre line so the lower half
# of the pillar stays solid (gives the fillet something to root in).
bore_channel = (
    cq.Workplane("XZ")
    .workplane(offset=-RING_WIDTH / 2.0)
    .center(0, RING_CENTRE_Z)
    .circle(BORE_R)
    .extrude(RING_WIDTH)
)

# Pillar that ties the collar down to the flange so the fillet has
# something to blend into.  Width = ring OD, depth = ring width.
pillar_w = RING_OD                     # along X
pillar_d = RING_WIDTH                  # along Y
pillar_h = RING_CENTRE_Z               # from flange bottom up to ring centre
pillar = (
    cq.Workplane("XY")
    .box(pillar_w, pillar_d, pillar_h, centered=(True, True, False))
)

# Clamp ears — two stacked blocks above the ring, separated by the
# slit.  Overlap the collar by 0.5 mm so the boolean fuse actually
# merges (CadQuery boolean fuse on tangentially-touching solids
# silently returns an empty Compound — see repo memory on the auger
# direct-drive build).
EAR_FUSE_OVERLAP = 0.5
ears = (
    cq.Workplane("XY")
    .box(
        EAR_THICK * 2 + SLIT_WIDTH,    # spans both ears + slit
        EAR_WIDTH,
        EAR_HEIGHT + EAR_FUSE_OVERLAP,
        centered=(True, True, False),
    )
    .translate((0, 0, RING_TOP_Z - EAR_FUSE_OVERLAP))
)

# Fuse the four solids together, then carve the bore channel out so
# the auger can pass through the collar without hitting the pillar.
bracket = flange.union(pillar).union(collar).union(ears)
bracket = bracket.cut(bore_channel)

# Smooth-transition fillet between the pillar sides and the flange
# top.  We fillet only the two long edges where the pillar's X-face
# walls meet the flange top — the front/back edges (along Y at Y=
# ±pillar_d/2) are broken into 3 segments by the bore cut, and
# filleting those segments diverges with OCCT.  The user-visible
# "smooth transition" arrow in the sketch points at the side, which
# is exactly this fillet.
fillet_eps = 0.05
try:
    bracket = bracket.edges(
        cq.selectors.BoxSelector(
            (+pillar_w / 2.0 - fillet_eps, -pillar_d / 2.0 - fillet_eps, FLANGE_T - fillet_eps),
            (+pillar_w / 2.0 + fillet_eps, +pillar_d / 2.0 + fillet_eps, FLANGE_T + fillet_eps),
        )
    ).fillet(FLANGE_FILLET)
    bracket = bracket.edges(
        cq.selectors.BoxSelector(
            (-pillar_w / 2.0 - fillet_eps, -pillar_d / 2.0 - fillet_eps, FLANGE_T - fillet_eps),
            (-pillar_w / 2.0 + fillet_eps, +pillar_d / 2.0 + fillet_eps, FLANGE_T + fillet_eps),
        )
    ).fillet(FLANGE_FILLET)
except Exception as exc:  # pragma: no cover — surface to operator on bad params
    print(f"[auger-bracket] fillet skipped: {exc}")

# 2 mm slit — Y-Z plane at x = 0, cuts top-down from above the ears
# down through both ears, through the ring wall, and into the bore so
# the clamp screw can actually pinch the ring shut.  Stops at the
# ring centre height so the lower half of the ring stays intact.
slit_top_z = RING_TOP_Z + EAR_HEIGHT + 1.0
slit_bottom_z = RING_CENTRE_Z       # stop at the bore centre
slit_height = slit_top_z - slit_bottom_z
slit = (
    cq.Workplane("XY")
    .box(
        SLIT_WIDTH,
        RING_WIDTH + 2.0,        # well past the collar ends
        slit_height,
        centered=(True, True, False),
    )
    .translate((0, 0, slit_bottom_z))
)
bracket = bracket.cut(slit)

# M3 clamp hole across the ears (along X).  Centre it vertically in
# the ears, axially in the ring.
clamp_z = RING_TOP_Z + CLAMP_HOLE_Z_FROM_RING_TOP
bracket = (
    bracket.faces(">X").workplane(origin=(0, 0, clamp_z))
    .circle(M3_CLEARANCE_D / 2.0)
    .cutThruAll()
)


# --------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------- #
def _solid(workplane: cq.Workplane) -> cq.Shape:
    """Return the single solid from a Workplane, raising if not unique."""
    solids = workplane.val().Solids() if workplane.val().ShapeType() != "Solid" else [workplane.val()]
    if len(solids) != 1:
        raise RuntimeError(f"expected exactly 1 solid, got {len(solids)}")
    return solids[0]


def main() -> None:
    here = Path(__file__).resolve().parent
    step_path = here / "auger-bracket.step"
    stl_path = here / "auger-bracket.stl"

    solid = _solid(bracket)
    cq.exporters.export(solid, str(step_path))
    cq.exporters.export(solid, str(stl_path), tolerance=0.05, angularTolerance=0.2)

    bb = solid.BoundingBox()
    print("Auger Bracket — geometry summary")
    print(f"  bounding box  : "
          f"X[{bb.xmin:+.2f}, {bb.xmax:+.2f}]  "
          f"Y[{bb.ymin:+.2f}, {bb.ymax:+.2f}]  "
          f"Z[{bb.zmin:+.2f}, {bb.zmax:+.2f}]  mm")
    print(f"  volume        : {solid.Volume() / 1000:.2f} cm^3")
    print(f"  bore diameter : {BORE_D:.2f} mm   (auger OD = {AUGER_OD:.2f} mm)")
    print(f"  STEP -> {step_path.relative_to(here.parent.parent)}")
    print(f"  STL  -> {stl_path.relative_to(here.parent.parent)}")


if __name__ == "__main__":
    main()
