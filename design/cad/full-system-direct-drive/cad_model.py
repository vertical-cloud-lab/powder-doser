"""Full powder-dosing system, direct-drive variant (issue #16, comment 4463659493).

Parametric CadQuery model of the full single-channel powder doser:

  * Vertical hollow auger barrel (FDM-printable, parametric tube).
  * Internal Archimedes auger (parametric pitch, flight thickness, turns).
  * Top: NEMA 11 mounting flange + ST-FC01 5x5 flexible-shaft coupler stub
    (direct drive — no gears, no belts).
  * Side hopper inlet neck just below the flange.
  * Near the dispense exit (within 25 mm of the bottom):
      - ERM disc pocket (Adafruit #1201, 10 x 2.7 mm) on +X side, with
        a 4 mm wire-exit channel routed up the housing.
      - JF-0530B solenoid pocket (Adafruit #412, ~9.6 x 19 x 22 mm) on
        -X side, oriented so the plunger taps the tube wall radially,
        with a 4 mm wire-exit channel routed up the housing.
      Both pockets are accessible from above (the print is paused, the
      part is dropped/epoxied in, the print resumes and encapsulates
      the body, with the wires routed out via the channels).
  * Below the dispense exit: a yoke that captures an HD-1810MG-class
    metal-gear servo (Adafruit #1142, 40.7 x 19.7 x 42.9 mm) so the
    servo's horn pivots a small deflector blade about the dispense
    axis, keeping the dispense point relatively fixed.
  * Back face: Raspberry Pi Zero 2 W mounting boss (65 x 30 mm
    footprint) with the four M2.5 through-holes on the official
    58 x 23 mm grid; the Pi + Perma-Proto Bonnet stack mounts here
    via standoffs (no pause-print embed for the electronics).

Exposed parameters (every value the prompt asked to be adjustable):

  * tube_outside_diameter        - "diameter of auger tube"
  * auger_flight_thickness       - "thickness of the auger stairs"
  * auger_pitch                  - "steepness of the auger stairs"
                                    (number of turns = tube_length / pitch)
  * tube_length                  - "length of the auger tube"
  * erm_diameter, erm_thickness  - "diameter and thickness of the ERM disc"
  * stepper_length, stepper_width, stepper_height
                                 - "stepper motor length, width, height"

Vendor part numbers and dimensions are sourced verbatim from
``hardware/vendor-files/`` on the
``copilot/identify-vibration-motor-solenoid-parts`` branch (StepperOnline
11HS18-0674S, ST-FC01, Adafruit #1201, #412, #1142, Raspberry Pi Zero 2 W
mechanical drawing). See README.md for the cross-reference table.

Outputs
-------
  * ``full_system.step`` - full-system BREP
  * ``full_system.stl`` - mesh of the same
  * ``stl/housing.stl``, ``stl/auger.stl``, ``stl/deflector.stl``,
    ``stl/coupler_stub.stl`` - per-part STLs for the slicer

Run from anywhere::

    python design/cad/full-system-direct-drive/cad_model.py

Requires ``cadquery`` (``pip install cadquery``).
"""
from __future__ import annotations

import math
import pathlib
from dataclasses import dataclass

import cadquery as cq

HERE = pathlib.Path(__file__).resolve().parent
STL_DIR = HERE / "stl"


@dataclass
class Params:
    # ---- adjustable per the comment ----
    tube_outside_diameter: float = 24.0   # auger barrel OD (mm)
    auger_flight_thickness: float = 1.6   # helix sheet thickness (mm)
    auger_pitch: float = 10.0             # mm/turn  (steepness; smaller = steeper)
    tube_length: float = 110.0            # barrel length (mm)
    erm_diameter: float = 10.0            # Adafruit #1201
    erm_thickness: float = 2.7            # Adafruit #1201
    stepper_length: float = 28.0          # NEMA 11 faceplate (11HS18-0674S)
    stepper_width: float = 28.0           # NEMA 11 faceplate
    stepper_height: float = 45.0          # NEMA 11 body length

    # ---- derived / fixed (vendor data, see README.md cross-reference) ----
    tube_wall: float = 2.0                # printed wall thickness
    auger_shaft_diameter: float = 5.0     # matches stepper shaft + ST-FC01 bore
    auger_clearance: float = 0.4          # radial slip-fit between flight tip and bore

    # NEMA 11 mounting (centred on the top of the tube)
    nema11_pilot_diameter: float = 22.0   # pilot through-hole for shaft + boss
    nema11_bolt_circle: float = 23.0      # 23 mm square pattern
    nema11_bolt_clearance: float = 2.8    # M2.5 clearance

    # ST-FC01 coupler envelope
    coupler_diameter: float = 18.0
    coupler_length: float = 25.0

    # Side hopper inlet
    hopper_diameter: float = 12.0
    hopper_offset_below_flange: float = 14.0

    # Embed pockets — placed within 25 mm of the bottom dispense exit
    embed_band_centre_above_exit: float = 14.0
    solenoid_x: float = 9.6
    solenoid_y: float = 19.0
    solenoid_z: float = 22.0
    solenoid_clearance: float = 0.3
    wire_channel_diameter: float = 4.0

    # Bottom exit
    dispense_exit_diameter: float = 4.0
    dispense_exit_chamfer: float = 1.0

    # Servo yoke (Adafruit #1142, HD-1810MG envelope)
    servo_x: float = 40.7
    servo_y: float = 19.7
    servo_z: float = 42.9
    servo_horn_radius: float = 12.0
    servo_axis_offset_below_exit: float = 18.0  # axial gap exit-to-servo-axis

    # Pi Zero 2 W mount (back face)
    pi_length: float = 65.0
    pi_width: float = 30.0
    pi_hole_grid_x: float = 58.0
    pi_hole_grid_y: float = 23.0
    pi_hole_clearance: float = 2.8
    pi_standoff_height: float = 4.0

    # Top mounting flange (square, holds the stepper)
    flange_size: float = 50.0
    flange_thickness: float = 6.0


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------


def make_auger(p: Params) -> cq.Workplane:
    """Central shaft + helical flight, sized to fit the bore with clearance."""
    bore_radius = (p.tube_outside_diameter - 2 * p.tube_wall) / 2.0
    flight_outer = bore_radius - p.auger_clearance
    flight_inner = p.auger_shaft_diameter / 2.0
    height = p.tube_length - 2.0  # leave 1 mm clearance at each end

    # Helical flight: sweep a thin radial rectangle along a helix.
    # The profile MUST be placed at the helix's starting radius on the XZ plane
    # — otherwise CadQuery's sweep interprets it as relative to the origin and
    # the resulting solid collapses to the central axis (bbox x=[-thickness/2,
    # +thickness/2] instead of spanning the helix diameter).
    # An additional small overlap with the shaft prevents the OCC fuse from
    # producing an empty Compound at the tangential boundary.
    overlap = 0.5
    radial_thickness = (flight_outer - flight_inner) + overlap
    helix_radius = (flight_inner - overlap / 2.0 + flight_outer) / 2.0
    helix = cq.Wire.makeHelix(pitch=p.auger_pitch, height=height,
                              radius=helix_radius)
    path = cq.Workplane(obj=helix)
    flight = (
        cq.Workplane("XZ")
        .center(helix_radius, 0)
        .rect(radial_thickness, p.auger_flight_thickness)
        .sweep(path, isFrenet=True)
    )

    # Build the shaft in two parts:
    #   - the in-tube section, height-matched to the helix (so the boolean
    #     fuse with the flight succeeds — OCC fails when the shaft extends
    #     well past the flight on a tangential boundary);
    #   - a top spindle extension that sticks up through the flange to be
    #     captured by the ST-FC01 coupler.
    shaft_in_tube = (
        cq.Workplane("XY")
        .circle(p.auger_shaft_diameter / 2.0)
        .extrude(height)
    )
    auger = shaft_in_tube.union(flight)

    spindle_top = (
        cq.Workplane("XY")
        .workplane(offset=height - 4.0)
        .circle(p.auger_shaft_diameter / 2.0)
        .extrude(p.flange_thickness + p.coupler_length / 2.0 + 4.0)
    )
    return auger.union(spindle_top)


def make_housing(p: Params) -> cq.Workplane:
    """Tube + top flange + side hopper neck + embed pockets + dispense exit
    + servo yoke + Pi mounting boss.

    The housing is built as a single solid so the slicer sees one
    continuous part; the embed pockets and wire channels are cut
    last."""
    bore_radius = (p.tube_outside_diameter - 2 * p.tube_wall) / 2.0
    outer_radius = p.tube_outside_diameter / 2.0

    # 1. Main tube (outer cylinder).  Z=0 is the dispense exit; tube extends up.
    tube = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .extrude(p.tube_length)
    )

    # 2. Top mounting flange (square plate centred on the tube axis).
    flange = (
        cq.Workplane("XY")
        .workplane(offset=p.tube_length)
        .rect(p.flange_size, p.flange_size)
        .extrude(p.flange_thickness)
    )

    # 3. Side hopper neck — short outward cylinder on +Y, broken into the bore.
    # Build it directly on the XZ-plane (normal = +Y), no rotation needed.
    hopper_z = p.tube_length - p.hopper_offset_below_flange
    hopper_neck = (
        cq.Workplane("XZ")
        .workplane(offset=outer_radius - 0.01)
        .center(0, hopper_z)
        .circle(p.hopper_diameter / 2.0 + p.tube_wall)
        .extrude(8.0)
    )

    # 4. Servo yoke below the dispense exit.  A rectangular "U" cradle
    # whose inside face captures the servo body.  The top of the yoke
    # overlaps the bottom of the tube by 1 mm so the boolean union of
    # tube+yoke produces a single connected solid.
    yoke_outer_x = p.servo_x + 6.0
    yoke_outer_y = p.servo_y + 6.0
    yoke_height = p.servo_z + 4.0
    yoke_z_top = 1.0  # overlap into the tube by 1 mm
    yoke_z_bot = yoke_z_top - yoke_height
    yoke_block = (
        cq.Workplane("XY")
        .workplane(offset=yoke_z_bot)
        .rect(yoke_outer_x, yoke_outer_y)
        .extrude(yoke_height)
    )

    # 5. Pi Zero 2 W mounting boss on the -Y face (back of housing).
    pi_thickness = 4.0
    # Place boss so its inner face overlaps the tube wall by 1 mm.
    pi_y_offset = -(outer_radius + pi_thickness / 2.0 - 1.0)
    pi_z_centre = p.tube_length / 2.0
    pi_boss = (
        cq.Workplane("XY")
        .workplane(offset=pi_z_centre - p.pi_length / 2.0)
        .center(0, pi_y_offset)
        .rect(p.pi_width + 4.0, pi_thickness)
        .extrude(p.pi_length)
    )

    body = tube.union(flange).union(hopper_neck).union(yoke_block).union(pi_boss)

    # ----- subtractive features -----

    # Bore down the centre of the tube + through the flange (for shaft access).
    bore = (
        cq.Workplane("XY")
        .workplane(offset=-1.0)
        .circle(bore_radius)
        .extrude(p.tube_length + p.flange_thickness + 2.0)
    )
    body = body.cut(bore)

    # NEMA 11 pilot bore + four M2.5 mounting clearance holes through flange.
    nema_pilot = (
        cq.Workplane("XY")
        .workplane(offset=p.tube_length - 0.1)
        .circle(p.nema11_pilot_diameter / 2.0)
        .extrude(p.flange_thickness + 0.2)
    )
    body = body.cut(nema_pilot)
    bc = p.nema11_bolt_circle / 2.0
    nema_bolts = (
        cq.Workplane("XY")
        .workplane(offset=p.tube_length - 0.1)
        .pushPoints([(bc, bc), (-bc, bc), (bc, -bc), (-bc, -bc)])
        .circle(p.nema11_bolt_clearance / 2.0)
        .extrude(p.flange_thickness + 0.2)
    )
    body = body.cut(nema_bolts)

    # Hopper inlet through the wall — bored through the neck stub on +Y.
    hopper_bore = (
        cq.Workplane("XZ")
        .workplane(offset=outer_radius - 1.0)
        .center(0, hopper_z)
        .circle(p.hopper_diameter / 2.0)
        .extrude(20.0)
    )
    body = body.cut(hopper_bore)

    # ----- embed pockets near the bottom -----
    band_z = p.embed_band_centre_above_exit  # centre height above dispense exit

    # ERM disc pocket on +X side (cylindrical, axis along +X, sized to the disc + clearance).
    erm_pocket_depth = p.erm_thickness + 0.4
    erm_pocket = (
        cq.Workplane("YZ")
        .workplane(offset=outer_radius - erm_pocket_depth)
        .center(0, band_z)
        .circle(p.erm_diameter / 2.0 + 0.2)
        .extrude(erm_pocket_depth + 0.2)
    )
    body = body.cut(erm_pocket)

    # ERM wire-exit channel — small bore from pocket vertically up to the flange underside.
    erm_wire = (
        cq.Workplane("XY")
        .workplane(offset=band_z)
        .center(outer_radius - erm_pocket_depth - 0.5, 0)
        .circle(p.wire_channel_diameter / 2.0)
        .extrude(p.tube_length - band_z - p.flange_thickness)
    )
    body = body.cut(erm_wire)

    # Solenoid pocket on -X side (rectangular, deep enough for the body).
    sol_pocket = (
        cq.Workplane("YZ")
        .workplane(offset=-(outer_radius - p.solenoid_z + 0.0))
        .center(0, band_z)
        .rect(p.solenoid_y + p.solenoid_clearance,
              p.solenoid_x + p.solenoid_clearance)
        .extrude(p.solenoid_z + 0.2)
    )
    body = body.cut(sol_pocket)

    # Solenoid wire-exit channel — small bore vertically up to the flange.
    sol_wire = (
        cq.Workplane("XY")
        .workplane(offset=band_z)
        .center(-(outer_radius - 1.5), 0)
        .circle(p.wire_channel_diameter / 2.0)
        .extrude(p.tube_length - band_z - p.flange_thickness)
    )
    body = body.cut(sol_wire)

    # Dispense exit (chamfered hole at the bottom).
    exit_hole = (
        cq.Workplane("XY")
        .workplane(offset=-1.0)
        .circle(p.dispense_exit_diameter / 2.0)
        .extrude(3.0)
    )
    body = body.cut(exit_hole)

    # Hollow the servo yoke so it actually captures the servo body.
    servo_cavity = (
        cq.Workplane("XY")
        .workplane(offset=yoke_z_bot - 0.1)
        .rect(p.servo_x + p.solenoid_clearance, p.servo_y + p.solenoid_clearance)
        .extrude(p.servo_z + 0.1)
    )
    body = body.cut(servo_cavity)

    # Pi mount: 4× M2.5 through-holes on a 58 x 23 grid through the boss.
    gx = p.pi_hole_grid_x / 2.0
    gy = p.pi_hole_grid_y / 2.0
    pi_holes = (
        cq.Workplane("XZ")
        .workplane(offset=pi_y_offset - pi_thickness / 2.0 - 0.1)
        .center(0, pi_z_centre)
        .pushPoints([(gy, gx), (-gy, gx), (gy, -gx), (-gy, -gx)])
        .circle(p.pi_hole_clearance / 2.0)
        .extrude(pi_thickness + 0.2)
    )
    body = body.cut(pi_holes)

    return body


def make_coupler_stub(p: Params) -> cq.Workplane:
    """ST-FC01-shape: an 18 mm OD x 25 mm cylinder with two 5 mm bores.
    Drawn as an envelope so the assembly preview shows the direct-drive
    coupling between the stepper shaft and the auger spindle."""
    cyl = (
        cq.Workplane("XY")
        .workplane(offset=p.tube_length + p.flange_thickness + 1.0)
        .circle(p.coupler_diameter / 2.0)
        .extrude(p.coupler_length)
    )
    bore = (
        cq.Workplane("XY")
        .workplane(offset=p.tube_length + p.flange_thickness)
        .circle(p.auger_shaft_diameter / 2.0 + 0.1)
        .extrude(p.coupler_length + 2.0)
    )
    return cyl.cut(bore)


def make_deflector(p: Params) -> cq.Workplane:
    """20 x 12 x 1.2 mm blade attached to the servo horn (rendered for context)."""
    horn_z = -p.servo_axis_offset_below_exit
    blade = (
        cq.Workplane("XY")
        .workplane(offset=horn_z - 0.6)
        .rect(20.0, 12.0)
        .extrude(1.2)
        .translate((0, 0, 0))
    )
    return blade


# ---------------------------------------------------------------------------
# Build + export
# ---------------------------------------------------------------------------


def build(params: Params | None = None) -> dict[str, cq.Workplane]:
    p = params or Params()
    parts = {
        "housing": make_housing(p),
        "auger": make_auger(p),
        "coupler_stub": make_coupler_stub(p),
        "deflector": make_deflector(p),
    }
    return parts


def export(parts: dict[str, cq.Workplane], out_dir: pathlib.Path = HERE) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    STL_DIR.mkdir(parents=True, exist_ok=True)

    # Per-part STLs (slicer-ready).
    for name, wp in parts.items():
        cq.exporters.export(wp, str(STL_DIR / f"{name}.stl"))

    # Full-system STEP via assembly (handles multi-solid parts cleanly).
    asm = cq.Assembly(name="powder_doser_full_system")
    for name, wp in parts.items():
        asm.add(wp, name=name)
    asm.save(str(out_dir / "full_system.step"))

    # Full-system STL: build a Compound of every part's solids (union can
    # fail on tangential contacts; Compound preserves geometry losslessly
    # for visualisation/slicing).
    all_solids = []
    for wp in parts.values():
        all_solids.extend(wp.val().Solids() if hasattr(wp.val(), "Solids") else [wp.val()])
    compound = cq.Compound.makeCompound(all_solids)
    cq.exporters.export(compound, str(out_dir / "full_system.stl"))

    print(f"Wrote {out_dir / 'full_system.step'}")
    print(f"Wrote {out_dir / 'full_system.stl'}")
    for name in parts:
        print(f"Wrote {STL_DIR / (name + '.stl')}")


def main() -> int:
    parts = build()
    export(parts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
