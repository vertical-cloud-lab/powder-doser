"""
Parametric CadQuery model of the §2.2 inward-pointing single-collection-point
dispense geometry. Exports a STEP file and an isometric SVG render.

Geometry (matches design/cad/inward-collection-cup/sketch_2d.py):

  * N = 12 dispense tubes
  * tube OD = 30 mm, bore = 12 mm, length = 110 mm
  * pitch circle diameter = 150 mm (radius 75 mm)
  * tubes tilted 30 deg from vertical, aimed inward
  * outlets ~80 mm above cup rim
  * shared collection cup: Ø80 OD / Ø70 ID, 35 mm tall
  * cup sits on a load-cell block (110 x 110 x 18 mm) on a base plate

This is a *schematic* model — the auger flighting, motor mounts, load-cell
flexure, and bracketing structure are intentionally not modelled. The intent
is to convey the spatial concept and check that the dimensions in §2.2 are
geometrically self-consistent.
"""
from pathlib import Path
import math

import cadquery as cq

# --- design constants (mm) ------------------------------------------------
N_CHANNELS = 12
TUBE_OD = 30.0
TUBE_ID = 12.0
TUBE_LEN = 110.0
PITCH_RADIUS = 75.0
CUP_OD = 80.0
CUP_ID = 70.0
CUP_HEIGHT = 35.0
CUP_WALL_BOTTOM = 4.0
LOAD_CELL_W = 110.0
LOAD_CELL_D = 110.0
LOAD_CELL_H = 18.0
BASE_W = 320.0
BASE_D = 320.0
BASE_H = 8.0
TUBE_TILT_DEG = 30.0
OUTLET_HEIGHT_ABOVE_CUP_RIM = 80.0
RESERVOIR_OD = 55.0
RESERVOIR_H = 70.0


# --- world coordinates ----------------------------------------------------
# Z=0 is the top of the base plate.
z_base_top = BASE_H
z_lc_top = z_base_top + LOAD_CELL_H
z_cup_bot = z_lc_top
z_cup_top = z_cup_bot + CUP_HEIGHT
z_outlet = z_cup_top + OUTLET_HEIGHT_ABOVE_CUP_RIM


# --- base plate + load cell + cup ----------------------------------------
base = (
    cq.Workplane("XY")
    .box(BASE_W, BASE_D, BASE_H, centered=(True, True, False))
)

load_cell = (
    cq.Workplane("XY")
    .workplane(offset=z_base_top)
    .box(LOAD_CELL_W, LOAD_CELL_D, LOAD_CELL_H, centered=(True, True, False))
)

cup_outer = (
    cq.Workplane("XY")
    .workplane(offset=z_cup_bot)
    .circle(CUP_OD / 2)
    .extrude(CUP_HEIGHT)
)
cup_cavity = (
    cq.Workplane("XY")
    .workplane(offset=z_cup_bot + CUP_WALL_BOTTOM)
    .circle(CUP_ID / 2)
    .extrude(CUP_HEIGHT - CUP_WALL_BOTTOM + 0.1)
)
cup = cup_outer.cut(cup_cavity)


# --- one dispense channel (auger tube + reservoir) ------------------------
def make_channel(theta_rad: float) -> cq.Workplane:
    """Build one dispense channel rotated to angle ``theta_rad`` about Z.

    The channel is constructed in its own local frame (channel axis along
    +X, outlet at origin) and then transformed into world coordinates so
    that the outlet sits on the pitch circle at z=z_outlet, with the axis
    tilted ``TUBE_TILT_DEG`` away from vertical (i.e. it leans outward and
    upward, with the bore pointing inward and downward at the cup).
    """
    # Build along local +Z: outlet at local origin, tube extends in +Z
    tube_solid = (
        cq.Workplane("XY")
        .circle(TUBE_OD / 2)
        .circle(TUBE_ID / 2)
        .extrude(TUBE_LEN)
    )
    # Reservoir (a closed cylinder) on top of the tube
    reservoir = (
        cq.Workplane("XY")
        .workplane(offset=TUBE_LEN + 2)
        .circle(RESERVOIR_OD / 2)
        .extrude(RESERVOIR_H)
    )
    channel = tube_solid.union(reservoir)

    # Tilt: rotate about Y so local +Z leans toward +X by TUBE_TILT_DEG
    # (after this, "up the tube" goes in the +x,+z direction).
    channel = channel.rotate((0, 0, 0), (0, 1, 0), TUBE_TILT_DEG)

    # Translate so the outlet ends up at (PITCH_RADIUS, 0, z_outlet) in world
    # coordinates, then rotate the whole channel about world Z by theta.
    channel = channel.translate((PITCH_RADIUS, 0, z_outlet))
    channel = channel.rotate((0, 0, 0), (0, 0, 1), math.degrees(theta_rad))
    return channel


channels = None
for i in range(N_CHANNELS):
    theta = 2 * math.pi * i / N_CHANNELS + math.pi / N_CHANNELS
    ch = make_channel(theta)
    channels = ch if channels is None else channels.union(ch)


# --- assembly with colors so the SVG export looks readable ---------------
asm = cq.Assembly(name="inward_collection_cup")
asm.add(base, name="base", color=cq.Color(0.85, 0.85, 0.85))
asm.add(load_cell, name="load_cell", color=cq.Color(0.6, 0.6, 0.6))
asm.add(cup, name="cup", color=cq.Color(1.0, 0.95, 0.7))
asm.add(channels, name="channels", color=cq.Color(0.55, 0.7, 0.95))


# --- exports --------------------------------------------------------------
out_dir = Path(__file__).parent
step_path = out_dir / "inward_collection_cup.step"
asm.save(str(step_path))
print(f"wrote {step_path}")

# Combined solid for the SVG render (Assembly SVG export is not as nice).
combined = base.union(load_cell).union(cup).union(channels)

# Isometric-ish SVG with hidden lines styled
opts_iso = {
    "width": 1200,
    "height": 900,
    "marginLeft": 10,
    "marginTop": 10,
    "showAxes": False,
    "projectionDir": (1.2, -1.0, 0.9),
    "strokeWidth": 0.4,
    "strokeColor": (20, 20, 20),
    "hiddenColor": (160, 160, 160),
    "showHidden": True,
}
svg_iso = out_dir / "inward_collection_cup_iso.svg"
cq.exporters.export(combined, str(svg_iso), opt=opts_iso)
print(f"wrote {svg_iso}")

# Top-down SVG
opts_top = dict(opts_iso)
opts_top["projectionDir"] = (0, 0, 1)
svg_top = out_dir / "inward_collection_cup_top.svg"
cq.exporters.export(combined, str(svg_top), opt=opts_top)
print(f"wrote {svg_top}")
