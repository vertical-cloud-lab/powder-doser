"""Phase 0 ground-truth auger model for the multi-part Zoo workflow.

Hand-authored CadQuery reference for PR #5 review comment 4464317865:
the *canonical* "auger + tube as one part, no hopper, no axial slab"
geometry that every Zoo-returned ``auger_solid`` part is graded against
in the Judge loop.

Geometry rules (locked in stone for the multi-part workflow):

* Outer tube: 24 mm OD, 2 mm wall, 100 mm long, fused with the flight
  into a single closed solid (no slip joint, no separate inner channel).
* Internal helical flight: outer radius 9.7 mm, central shaft 6 mm,
  10 mm pitch, 1.6 mm thick, single-start, 10 turns over 100 mm.
* Top: M3 tap drill (Ø2.5 mm) on axis, 6 mm deep into the spindle.
* Bottom: Ø2.5 mm exit hole on axis, all the way through the floor.
* No hopper. No axial slab. The bore *is* the powder volume; the auger
  flight occupies it and conveys powder by rotation.

See also the failure-mode notes in the iteration cad_model.py:
``cadquery boolean fuse`` (need 0.5 mm radial overlap on shaft⇄flight)
and ``cadquery helix sweep`` (need .center(helix_radius, 0) before
.sweep(path) or the flight collapses to the central axis).

Outputs: ``ground_truth_auger.step`` + ``ground_truth_auger.stl``.
"""
from __future__ import annotations

import pathlib

import cadquery as cq

HERE = pathlib.Path(__file__).resolve().parent

# Locked geometry — keep in sync with the prompt in
# zoo_multi_part_probe.py PARTS["auger_solid"].
TUBE_OD = 24.0
TUBE_WALL = 2.0
TOTAL_H = 100.0
FLIGHT_R = 10.0  # = tube ID/2 — flight fuses directly to inner tube wall
SHAFT_D = 6.0
SHAFT_R = SHAFT_D / 2
PITCH = 10.0
FLIGHT_THK = 1.6
M3_TAP_D = 2.5  # M3 tap drill ≈ 2.5 mm
M3_DEPTH = 6.0
EXIT_D = 2.5
SHAFT_FLIGHT_OVERLAP = 0.5  # see "cadquery boolean fuse" memo


def make_outer_tube() -> cq.Workplane:
    """Hollow outer tube (annular shell, OD - ID = 2*wall)."""
    return (
        cq.Workplane("XY")
        .circle(TUBE_OD / 2)
        .circle(TUBE_OD / 2 - TUBE_WALL)
        .extrude(TOTAL_H)
    )


def make_shaft() -> cq.Workplane:
    return cq.Workplane("XY").circle(SHAFT_R).extrude(TOTAL_H)


def make_flight() -> cq.Workplane:
    """Helical flight, swept rectangular profile.

    The .center(helix_radius, 0) shift is required because a bare
    rect().sweep(helix) collapses the rectangle onto the central axis
    (CadQuery 2.7 behaviour, see helix-sweep memo).
    """
    radial_thickness = (FLIGHT_R - SHAFT_R) + SHAFT_FLIGHT_OVERLAP
    helix_radius = (SHAFT_R - SHAFT_FLIGHT_OVERLAP / 2.0 + FLIGHT_R) / 2.0
    helix = cq.Wire.makeHelix(pitch=PITCH, height=TOTAL_H, radius=helix_radius)
    path = cq.Workplane(obj=helix)
    return (
        cq.Workplane("XZ")
        .center(helix_radius, 0)
        .rect(radial_thickness, FLIGHT_THK)
        .sweep(path, isFrenet=True)
    )


def build() -> cq.Workplane:
    tube = make_outer_tube()
    shaft = make_shaft()
    flight = make_flight()
    # Fuse shaft + flight into one solid (small overlap defeats the
    # CadQuery tangential-fuse-returns-empty-Compound bug).
    inner = shaft.union(flight, glue=False)
    # Fuse tube + inner; then bore the central axial holes.
    body = tube.union(inner, glue=False)
    # Tap drill + exit hole: cut as cylindrical tools rather than relying
    # on face selection (the fused top has helical (non-planar) faces from
    # the flight's terminal turn that confuse `.faces(">Z").workplane()`).
    tap_tool = (
        cq.Workplane("XY")
        .workplane(offset=TOTAL_H - M3_DEPTH)
        .circle(M3_TAP_D / 2)
        .extrude(M3_DEPTH + 0.01)
    )
    exit_tool = (
        cq.Workplane("XY")
        .workplane(offset=-0.01)
        .circle(EXIT_D / 2)
        .extrude(TOTAL_H + 0.02)
    )
    body = body.cut(tap_tool).cut(exit_tool)
    return body


def main() -> int:
    out = build()
    step_path = HERE / "ground_truth_auger.step"
    stl_path = HERE / "ground_truth_auger.stl"
    cq.exporters.export(out, str(step_path))
    cq.exporters.export(out, str(stl_path))
    bb = out.val().BoundingBox()
    n_solids = len(out.val().Solids())
    print(f"wrote {step_path.name}  ({step_path.stat().st_size} bytes)")
    print(f"wrote {stl_path.name}   ({stl_path.stat().st_size} bytes)")
    print(f"bbox: ({bb.xlen:.2f} × {bb.ylen:.2f} × {bb.zlen:.2f}) mm")
    print(f"solids: {n_solids}  (expect 1 — single fused body)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
