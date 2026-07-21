"""Parametric CAD model of the powder-excavator (CadQuery / open-source).

This is the start of a **feedback-loop friendly** CAD pipeline for the
powder-excavator design described in ``docs/manuscript/main.tex``. CadQuery
was chosen over closed-source authoring tools (Rhino + Grasshopper, Fusion
Generative Design, nTop, Onshape FeatureScript) because it is

* pure Python and pip-installable on every major OS,
* fully scripted (no GUI required for parametric updates), so a design
  iteration is just a ``git diff`` and a re-run, and
* produces standards-compliant STEP and STL output that any open-source
  slicer (PrusaSlicer, OrcaSlicer, Cura) can consume.

The single source of truth for every dimension is :class:`ExcavatorParams`.
Changing one number there propagates through every part.

Usage
-----

Build all parts and the assembly to ``cad/build/`` (run from the repo root)::

    python -m cad.build

Run the design-for-manufacturing checks (per-part wall thickness, FDM
overhang angles, gantry-only kinematics)::

    python -m cad.dfm

Both modules import :func:`build_assembly` from this file, so the same
parametric model drives both the export and the feedback checks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import cadquery as cq

# Type alias for cadquery objects we hand back to the caller.
CQObject = Any


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExcavatorParams:
    """All design parameters for the powder-excavator, in millimetres.

    Defaults match the dimensions called out in the README and
    ``docs/manuscript/main.tex`` for the longitudinal-pivot, sideways-tilt
    geometry (trough length L = 80 mm, L ~ 3 D, etc.). Mutating values is
    forbidden so the model is reproducible: build a new instance instead.
    """

    # ----- trough (the half-cylinder ladle, open at the top) -----
    trough_length: float = 80.0           # L, along the long pivot axis
    trough_radius: float = 13.0           # inner radius of the half-cylinder
    trough_wall: float = 1.6              # printed wall thickness
    end_cap_thickness: float = 2.0        # closed end caps at +/- L/2

    # ----- pivot (a metal dowel pin running along L through both end caps) -
    pin_diameter: float = 3.0
    # Diametral clearance for the printed pivot hole. 0.3 mm is the lower
    # end of the standard FDM sliding-fit window (0.3-0.4 mm); 0.2 mm
    # was found to fuse / bind in print (Edison v3 analysis, docs/edison/
    # analysis-v3-longitudinal-tilt-cad.md sec. 3).
    pin_clearance: float = 0.3
    pivot_boss_diameter: float = 8.0      # local boss around the pin hole
    pivot_boss_thickness: float = 4.0
    # Y-coordinate of the pivot pin axis in trough-local coords (rim is at
    # Y = 0, half-cylinder hangs into -Y). To keep the loaded trough as a
    # *stable* pendulum, the pivot has to sit ABOVE the loaded centre of
    # gravity. For a half-cylinder filled with powder, the powder centroid
    # is at -4 r / (3 pi) ~ -5.5 mm for r = 13 mm; combined with the shell
    # and small rim lips the loaded CG is around -5 mm. Putting the pivot
    # at Y = -4 mm keeps it ~1 mm above the loaded CG (stable) while
    # leaving the 8 mm pivot boss fully inscribed in the half-disk
    # end-cap envelope. (Edison v3 sec. 1, "Inverted Pendulum" flaw.)
    pivot_offset_y: float = -4.0

    # ----- arms (two parallel verticals dropping from the gantry) -----
    # Axis assignments below match :func:`build_arm`: the arm's wide face
    # (``arm_width``) is along X (perpendicular to both Y and the pin
    # axis), giving good bending stiffness against the cam reaction load.
    # The arm is thin along Z (``arm_thickness``), which is the trough's
    # longitudinal pin axis. ``arm_length`` is the vertical drop in Y
    # from the carriage down to the pin-hole height.
    arm_thickness: float = 4.0            # along Z (pin axis = along trough length L)
    arm_width: float = 8.0                # along X (perpendicular face), must clear pivot boss
    arm_length: float = 60.0              # vertical drop from carriage (Y)
    arm_gap: float = 1.0                  # gap between arm inside face and trough end cap

    # ----- chamfered rim lip on the trough (defines the pour edge AND
    #       engages the cam ramp) -----
    # The lip runs continuously along the full trough length L on BOTH
    # long-side rims (the trough is symmetric, so it can dump in either
    # direction; whichever rim is on the cam-side becomes the "bumper" for
    # that stroke). A continuous lip — rather than a localised spout —
    # avoids reintroducing a powder-arching bottleneck at the pour edge,
    # while the chamfer (a) detaches the powder stream cleanly, (b) defines
    # a sharp geometric tip-over angle (better dose-vs-tilt repeatability),
    # and (c) provides a low-overhang printable surface for the cam to
    # ride on.
    #
    # Lip cross-section is kept SMALL (2 x 2 mm with a 1 mm chamfer): the
    # earlier 6 x 6 mm lips added ~7 g of PETG well above the rim and
    # pushed the loaded CG above the pivot, ruining pendulum stability.
    # (Edison v3 sec. 1 + sec. 3, lip geometry.)
    bumper_height: float = 2.0            # radial protrusion of the lip
    bumper_chamfer: float = 1.0           # outside-edge chamfer dimension
    bumper_width: float = 2.0             # lip thickness in X (cross-section)

    # ----- fixed bed-edge strike-off bar -----
    strike_off_length: float = 100.0      # spans the bed edge
    strike_off_section: float = 4.0       # square cross-section side

    # ----- smooth inclined cam ramp (baseline tilt actuator) -----
    # NB Edison v3 sec. 1 flagged the cam ramp as kinematically marginal
    # (snap-through singularity past ~40 deg, cam_ramp_rise was wasted
    # above the lever's max reach). The pin-slot variant (Panel E) is
    # therefore the recommended baseline; the cam ramp is kept here as
    # a fallback option whose dimensions are clamped to the
    # max-achievable lift (~R*(sin(target+phi0)-sin(phi0))) instead of
    # an unreachable 20 mm. dfm.py's physics.cam.rise_utilisation check
    # enforces this.
    cam_ramp_length: float = 35.0         # along gantry X
    cam_ramp_rise: float = 10.0           # vertical rise across the ramp (within lever's reach)
    cam_ramp_width: float = 10.0          # along gantry Y
    cam_ramp_thickness: float = 8.0       # below the running surface

    # ----- pin-slot variant (per PXL_20260423_231729467.jpg, manuscript Sec. ``Pin-defined-path actuation'') -----
    slot_board_length: float = 220.0      # along gantry X
    slot_board_height: float = 60.0       # along gantry Z
    slot_board_thickness: float = 6.0     # along gantry Y
    slot_width: float = 4.2               # peg diameter + clearance
    slot_depth: float = 5.0               # routed depth into the board
    # Polyline of (X, Z) waypoints describing the slot path on the board, in
    # the board's local frame (origin at the bottom-left corner of the board).
    # Default is the same path baked into ``panel-E-pin-slot.svg``: flat for
    # the scoop+transport stretch, rising over the deposit station.
    slot_path: tuple[tuple[float, float], ...] = (
        (10.0, 30.0),
        (140.0, 30.0),
        (170.0, 24.0),
        (200.0, 12.0),
        (210.0, 12.0),
    )

    # ----- gantry working envelope (used by dfm.py's kinematic checks) -----
    gantry_x_travel: float = 250.0
    gantry_z_travel: float = 80.0

    # ----- physics-of-mechanism feedback targets (used by dfm.py) -----
    # Target useful tilt angle for the cam ramp (deg from horizontal). The
    # cam ramp must be able to drive the trough this far before the
    # tilt-vs-X sensitivity saturates (snap-through singularity).
    cam_target_tilt_deg: float = 45.0
    # Maximum acceptable d(theta)/d(X) sensitivity for the cam ramp at the
    # target tilt, in deg per mm of gantry X travel. >15 deg/mm makes
    # metered pouring uncontrollable. (Edison v3 sec. 1, "Cam Singularity"
    # flaw and sec. 4, dfm.py shortfalls.)
    cam_sensitivity_ceiling_deg_per_mm: float = 15.0
    # Maximum acceptable change in slot direction at any waypoint, in
    # degrees. Sharp corners spike the normal force on the peg and make
    # the slot bind. (Edison v3 sec. 4, pin-slot friction.)
    slot_max_corner_deg: float = 60.0
    # Powder bulk density (g/cm^3) used for the loaded centre-of-gravity
    # calculation in the pendulum-stability check. 1.0 g/cm^3 is a
    # reasonable default for inorganic powders at packed bulk density.
    powder_bulk_density: float = 1.0
    # Print material density (g/cm^3) used for the loaded CG calculation.
    # 1.27 g/cm^3 is PETG; PLA is 1.24, nylon 1.14.
    print_material_density: float = 1.27

    # ----- FDM-printability targets (used by dfm.py's printability checks) -
    min_wall: float = 0.8                 # absolute minimum FDM wall (4-perimeter @ 0.2 mm)
    max_overhang_deg: float = 50.0        # measured from vertical; >50 needs supports

    # Optional metadata (e.g. the git SHA of the design used). Excluded from
    # geometry but useful when the build script writes a manifest.
    metadata: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Individual parts
# ---------------------------------------------------------------------------


def _half_disk_solid(radius: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .moveTo(-radius, 0)
        .lineTo(radius, 0)
        .threePointArc((0, -radius), (-radius, 0))
        .close()
    )


def build_trough(p: ExcavatorParams) -> CQObject:
    """The open-top half-cylinder ladle with closed end caps and pivot bosses.

    The trough is built lying along the +Z axis (length L along Z), with its
    open top facing +Y, so that the longitudinal pivot pin runs through the
    centre of the two end caps along Z.
    """
    # Outer solid (full length, full outer radius)
    outer = _half_disk_solid(p.trough_radius + p.trough_wall).extrude(p.trough_length)
    # Inner cavity (full outer minus end caps -> length L - 2 * cap)
    cavity_len = p.trough_length - 2 * p.end_cap_thickness
    cavity = (
        _half_disk_solid(p.trough_radius)
        .extrude(cavity_len)
        .translate((0, 0, p.end_cap_thickness))
    )
    body = outer.cut(cavity)

    # Pivot bosses sit on the OUTSIDE of each end cap. Their axis is along
    # Z. We place them on the longitudinal centre line of the half-cylinder
    # at (X=0, Y=p.pivot_offset_y); ``pivot_offset_y`` is chosen above the
    # loaded CG to give a stable pendulum (Edison v3 sec. 1).
    pivot_centre_y = p.pivot_offset_y
    boss = (
        cq.Workplane("XY")
        .center(0, pivot_centre_y)
        .circle(p.pivot_boss_diameter / 2)
        .extrude(p.pivot_boss_thickness)
    )
    boss0 = boss.translate((0, 0, -p.pivot_boss_thickness))
    boss1 = boss.translate((0, 0, p.trough_length))

    # Drill the pin clearance hole through caps + bosses (one pass along Z).
    pin_hole_len = p.trough_length + 2 * p.pivot_boss_thickness + 2.0
    pin_hole = (
        cq.Workplane("XY")
        .center(0, pivot_centre_y)
        .circle((p.pin_diameter + p.pin_clearance) / 2)
        .extrude(pin_hole_len)
        .translate((0, 0, -p.pivot_boss_thickness - 1.0))
    )

    # Continuous chamfered lip on each long-side rim, running the full
    # trough length L. Replaces the localised mid-length "bumper": a
    # localised spout would reintroduce a powder-arching bottleneck at the
    # pour edge (cf. Edison v2 §3 on the 90° V-pocket retention problem).
    # The lip is symmetric (one per long side) so the trough can dump
    # either way and either rim can be the cam-engagement surface; the
    # outside chamfer on each lip is what actually rides up the cam ramp
    # and what defines the pour edge's tip-over angle.
    outer_r = p.trough_radius + p.trough_wall
    lip_x_centre = outer_r - p.bumper_width / 2

    def _make_lip(sign: int) -> CQObject:
        # ``sign`` is +1 for the right rim, -1 for the left rim.  The
        # chamfered edge is the OUTER top edge (the one furthest from the
        # trough centre line, on the +Y side), since that is what the cam
        # ramp rides on and what the powder stream detaches from.
        lip = (
            cq.Workplane("XY")
            .box(
                p.bumper_width,        # X (lip thickness, sits on the rim wall)
                p.bumper_height,       # Y (radial protrusion above the rim)
                p.trough_length,       # Z (runs the full length L)
                centered=(True, False, False),
            )
        )
        outer_edge = ">X and >Y" if sign > 0 else "<X and >Y"
        lip = lip.edges(outer_edge).chamfer(p.bumper_chamfer)
        return lip.translate((sign * lip_x_centre, 0, 0))

    lip_right = _make_lip(+1)
    lip_left = _make_lip(-1)

    return body.union(boss0).union(boss1).union(lip_right).union(lip_left).cut(pin_hole)


def build_arm(p: ExcavatorParams) -> CQObject:
    """One vertical arm.

    Two of these are mirrored about z = L/2 to grip the trough's two end
    caps. The arm hangs from a carriage above it (not modelled here) down
    to the pivot pin at its lower end. In model coordinates:

    * +Y is the trough's open-top direction (and also "world up"), so the
      arm extends from Y = 0 (its pin-hole height, which is placed at the
      pivot height in :func:`build_assembly`) up in +Y to the carriage.
    * +Z is the trough's longitudinal pin axis, so the arm is thin along
      Z (``arm_thickness``) and the pin clearance hole runs along Z too.
    * The arm's wide face (``arm_width``) is along X, perpendicular to
      both, giving good bending stiffness against the cam reaction load.
    """
    arm = (
        cq.Workplane("XY")
        .box(
            p.arm_width,        # X (wide face — bending stiffness)
            p.arm_length,       # Y (vertical drop from gantry carriage)
            p.arm_thickness,    # Z (along pin axis = along trough length L)
            centered=(True, False, True),
        )
    )
    # Pin clearance hole at the bottom of the arm (Y = 0 in arm-local
    # coords), drilled along +Z so it matches the pin's axis. Extruded
    # ``both=True`` so it punches all the way through the arm regardless
    # of arm_thickness.
    pin_hole = (
        cq.Workplane("XY")
        .circle((p.pin_diameter + p.pin_clearance) / 2)
        .extrude(p.arm_thickness * 2, both=True)
    )
    return arm.cut(pin_hole)


def build_pin(p: ExcavatorParams) -> CQObject:
    """Stock metal dowel pin (the pivot)."""
    total_length = (
        p.trough_length
        + 2 * p.pivot_boss_thickness
        + 2 * (p.arm_gap + p.arm_thickness)
    )
    return (
        cq.Workplane("XY")
        .circle(p.pin_diameter / 2)
        .extrude(total_length)
    )


def build_strike_off_bar(p: ExcavatorParams) -> CQObject:
    """The fixed bed-edge strike-off bar (square cross-section)."""
    return (
        cq.Workplane("XY")
        .box(p.strike_off_section, p.strike_off_length, p.strike_off_section)
    )


def build_cam_ramp(p: ExcavatorParams) -> CQObject:
    """The fixed smooth inclined cam ramp the bumper rides up.

    Built as a triangular prism plus a flat mounting base.
    """
    triangle = (
        cq.Workplane("XZ")
        .moveTo(0, 0)
        .lineTo(p.cam_ramp_length, 0)
        .lineTo(p.cam_ramp_length, p.cam_ramp_rise)
        .close()
    )
    ramp = triangle.extrude(p.cam_ramp_width)
    base = (
        cq.Workplane("XY")
        .box(
            p.cam_ramp_length,
            p.cam_ramp_width,
            p.cam_ramp_thickness,
            centered=(False, False, False),
        )
        .translate((0, 0, -p.cam_ramp_thickness))
    )
    return ramp.union(base)


def build_slot_board(p: ExcavatorParams) -> CQObject:
    """Routed slot board for the pin-defined-path actuation variant.

    The board is a rectangular slab with a slot routed along the polyline
    given by ``params.slot_path``. The slot is a fixed-width channel of
    depth ``slot_depth`` routed in from the +Y face of the board (the
    face the peg engages). The peg on the trough's stem rides inside it.
    If ``slot_depth >= slot_board_thickness`` the slot becomes a
    through-slot.
    """
    board = (
        cq.Workplane("XZ")
        .box(p.slot_board_length, p.slot_board_height, p.slot_board_thickness)
    )
    # Cut depth is clamped at the board thickness (a routed slot deeper
    # than the board itself just becomes a through-slot, not a cut into
    # both faces).
    cut_depth = min(p.slot_depth, p.slot_board_thickness)
    # Y-centre of the cut so it removes material from the +Y face inward
    # by exactly ``cut_depth`` (board is centred on Y=0 with thickness
    # ``slot_board_thickness``, so its +Y face is at +thickness/2).
    cut_y_centre = p.slot_board_thickness / 2 - cut_depth / 2
    # Build the slot as the union of "fat segments" (one per polyline edge),
    # avoiding CadQuery's arbitrary-path sweep which is brittle across
    # versions.
    slot_solid: CQObject = None
    for (x0, z0), (x1, z1) in zip(p.slot_path, p.slot_path[1:]):
        wx0 = x0 - p.slot_board_length / 2
        wz0 = z0 - p.slot_board_height / 2
        wx1 = x1 - p.slot_board_length / 2
        wz1 = z1 - p.slot_board_height / 2
        seg_len = math.hypot(wx1 - wx0, wz1 - wz0)
        if seg_len <= 0:
            continue
        ang_deg = math.degrees(math.atan2(wz1 - wz0, wx1 - wx0))
        seg = (
            cq.Workplane("XZ")
            .box(
                seg_len + p.slot_width,
                p.slot_width,
                cut_depth,
                centered=(True, True, True),
            )
        )
        seg = seg.rotate((0, 0, 0), (0, 1, 0), -ang_deg)
        seg = seg.translate(((wx0 + wx1) / 2, cut_y_centre, (wz0 + wz1) / 2))
        slot_solid = seg if slot_solid is None else slot_solid.union(seg)
    if slot_solid is not None:
        board = board.cut(slot_solid)
    return board


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def build_assembly(p: ExcavatorParams | None = None) -> cq.Assembly:
    """Build the full assembly (trough + two arms + pin)."""
    p = p or ExcavatorParams()
    trough = build_trough(p)
    arm = build_arm(p)
    pin = build_pin(p)

    asm = cq.Assembly(name="powder_excavator")
    asm.add(trough, name="trough", color=cq.Color(0.7, 0.7, 0.75))

    pivot_centre_y = p.pivot_offset_y
    arm_outer_z0 = -p.pivot_boss_thickness - p.arm_gap - p.arm_thickness / 2
    arm_outer_z1 = (
        p.trough_length + p.pivot_boss_thickness + p.arm_gap + p.arm_thickness / 2
    )
    asm.add(
        arm,
        name="arm_left",
        loc=cq.Location(cq.Vector(0, pivot_centre_y, arm_outer_z0)),
        color=cq.Color(0.4, 0.4, 0.45),
    )
    asm.add(
        arm,
        name="arm_right",
        loc=cq.Location(cq.Vector(0, pivot_centre_y, arm_outer_z1)),
        color=cq.Color(0.4, 0.4, 0.45),
    )
    asm.add(
        pin,
        name="pin",
        loc=cq.Location(cq.Vector(
            0, pivot_centre_y,
            -(p.pivot_boss_thickness + p.arm_gap + p.arm_thickness),
        )),
        color=cq.Color(0.85, 0.2, 0.2),
    )

    return asm


__all__ = [
    "ExcavatorParams",
    "build_arm",
    "build_assembly",
    "build_cam_ramp",
    "build_pin",
    "build_slot_board",
    "build_strike_off_bar",
    "build_trough",
]
