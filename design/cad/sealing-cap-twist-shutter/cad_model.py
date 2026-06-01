"""
Parametric CadQuery model — Twist-Shutter Sealing Cap (Concept §2.1 of
design/cap-brainstorming.md).

REVISION addressing PR #37 review (@swcharles):
  > I see a common axis in the twist shutter design, but not a clear
  > way to put them together. What do you see going there? A screw?
  > Otherwise it's just two plates put together, so they fall apart
  > instantly.

Yes — it's an M3 pan-head screw + M3 hex nut on a central pivot. The
upper (channel) disc has a Ø3.4 through-bore + a Ø6 × 2 mm counterbore
on its top face for the screw head. The lower (driver) disc has a
Ø3.4 through-bore opening into a captive hex pocket (5.5 mm AF × 3 mm
deep) on its bottom face for the nut. The screw is tightened just
enough that the discs can rotate but won't fall apart.

This revision:
  * Replaces the loose Ø4 pivot bore with a real M3 fastener bore set
    (counterbore on top, hex pocket on bottom).
  * Adds an M3 screw + M3 nut to the assembly so the renders show how
    the discs are clamped.
  * Adds an exploded-view render along the +Z axis.
  * Keeps the same overall geometry so the brainstorming numbers still
    apply.

Coordinate frame:
  +Z = up (towards the auger), Z = 0 at the bottom of the lower disc.
  All dimensions in millimetres.
"""

from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq

OUT = Path(__file__).parent
RENDER = OUT / "renders"
STL = OUT / "stl"
RENDER.mkdir(exist_ok=True)
STL.mkdir(exist_ok=True)


# --- Auger / channel interface (PR-#16) ------------------------------------
AUGER_OD = 25.0
EXIT_HOLE_D = 3.0

# --- Disc geometry ---------------------------------------------------------
CAP_OD = 36.0
DISC_T = 4.0
RIM_LIP_H = 3.0
RIM_LIP_T = 1.6

# --- M3 fastener (the pivot screw) -----------------------------------------
M3_CLEAR_D = 3.4         # M3 clearance bore (loose for rotation)
M3_HEAD_D = 6.0          # pan-head clearance
M3_HEAD_H = 2.0          # counterbore depth on the upper-disc top face
M3_NUT_AF = 5.5          # M3 hex nut across-flats
M3_NUT_H = 2.5           # nut thickness
NUT_POCKET_DEPTH = 3.0   # hex pocket depth on the lower-disc bottom face
M3_SHANK_LEN = 12.0      # screw shank length (unthreaded portion in the model)

# --- Slot geometry (sector through both discs) -----------------------------
SLOT_INNER_R = 4.0
SLOT_OUTER_R = 8.0
SLOT_ANGLE = 60.0        # sweep in degrees

# Twist between closed (slots 180° apart) and open (aligned).
TWIST_OPEN_DEG = 60.0

# --- Driver-disc actuation tab ---------------------------------------------
TAB_W = 6.0
TAB_L = 14.0
TAB_T = 3.0


# ============================================================================
# Disc builder
# ============================================================================

def _sector_cutter(angle_offset: float, height: float) -> cq.Workplane:
    """A pie-wedge cutter (the slot) at the given angular position."""
    half = SLOT_ANGLE / 2.0
    pts_outer = [(0.0, 0.0)]
    pts_inner = [(0.0, 0.0)]
    steps = 24
    for i in range(steps + 1):
        a = math.radians(-half + i * SLOT_ANGLE / steps)
        pts_outer.append((SLOT_OUTER_R * math.cos(a),
                          SLOT_OUTER_R * math.sin(a)))
        pts_inner.append((SLOT_INNER_R * math.cos(a),
                          SLOT_INNER_R * math.sin(a)))
    pts_outer.append((0.0, 0.0))
    pts_inner.append((0.0, 0.0))

    outer = cq.Workplane("XY").polyline(pts_outer).close().extrude(height)
    inner = cq.Workplane("XY").polyline(pts_inner).close().extrude(height)
    cut = outer.cut(inner)
    return cut.rotate((0, 0, 0), (0, 0, 1), angle_offset)


def upper_disc() -> cq.Workplane:
    """Channel-side disc — slot at 0°, snap lip + screw counterbore on top."""
    disc = cq.Workplane("XY").circle(CAP_OD / 2).extrude(DISC_T)
    # Pivot through-bore
    disc = (
        disc.faces(">Z").workplane()
        .moveTo(0, 0).hole(M3_CLEAR_D)
    )
    # Counterbore on top face for the M3 screw head
    disc = (
        disc.faces(">Z").workplane(invert=False)
        .moveTo(0, 0).cboreHole(M3_CLEAR_D, M3_HEAD_D, M3_HEAD_H)
    )
    # Sector slot
    disc = disc.cut(_sector_cutter(angle_offset=0.0, height=DISC_T))
    # Snap lip on top to grip the auger OD
    lip_outer_r = AUGER_OD / 2 + RIM_LIP_T
    lip = (
        cq.Workplane("XY")
        .workplane(offset=DISC_T)
        .circle(lip_outer_r)
        .circle(AUGER_OD / 2)
        .extrude(RIM_LIP_H)
    )
    return disc.union(lip)


def lower_disc(open: bool = False) -> cq.Workplane:
    """Driver disc — captive hex pocket on bottom, actuation tab on rim."""
    disc = cq.Workplane("XY").circle(CAP_OD / 2).extrude(DISC_T)

    # Pivot through-bore
    disc = (
        disc.faces(">Z").workplane()
        .moveTo(0, 0).hole(M3_CLEAR_D)
    )
    # Hex pocket on the bottom face captive of the nut. Use a hex
    # polygon cut.
    nut_radius = M3_NUT_AF / math.sqrt(3.0) * 1.05  # circumscribed + 5% slop
    hex_pts = []
    for i in range(6):
        a = math.radians(60 * i)
        hex_pts.append((nut_radius * math.cos(a), nut_radius * math.sin(a)))
    nut_pocket = (
        cq.Workplane("XY")
        .polyline(hex_pts).close()
        .extrude(NUT_POCKET_DEPTH)
    )
    disc = disc.cut(nut_pocket)

    # Sector slot — at the offset that gives "closed" (180°) or "open" (120°).
    angle = 180.0 - TWIST_OPEN_DEG if open else 180.0
    disc = disc.cut(_sector_cutter(angle_offset=angle, height=DISC_T))

    # Actuation tab — radial paddle aligned with the slot's bisector,
    # so the visual & mechanical state match.
    tab = (
        cq.Workplane("XY")
        .box(TAB_L, TAB_W, TAB_T, centered=(False, True, False))
        .translate((CAP_OD / 2 - 1.0, 0, (DISC_T - TAB_T) / 2))
    )
    tab = tab.rotate((0, 0, 0), (0, 0, 1), angle)
    return disc.union(tab)


# ============================================================================
# M3 fastener placeholders
# ============================================================================

def m3_screw(length: float = M3_SHANK_LEN) -> cq.Workplane:
    """Visual M3 pan-head screw — head at z=length, shank from 0 to length."""
    head = (
        cq.Workplane("XY")
        .workplane(offset=length)
        .circle(M3_HEAD_D / 2)
        .extrude(M3_HEAD_H)
    )
    shank = (
        cq.Workplane("XY")
        .circle(3.0 / 2)
        .extrude(length)
    )
    return head.union(shank)


def m3_nut() -> cq.Workplane:
    """Visual M3 hex nut."""
    nut_radius = M3_NUT_AF / math.sqrt(3.0)
    pts = []
    for i in range(6):
        a = math.radians(60 * i)
        pts.append((nut_radius * math.cos(a), nut_radius * math.sin(a)))
    nut_body = cq.Workplane("XY").polyline(pts).close().extrude(M3_NUT_H)
    nut_body = nut_body.faces(">Z").workplane().hole(3.0)
    return nut_body


# ============================================================================
# Auger reference stub
# ============================================================================

def auger_stub() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .workplane(offset=2 * DISC_T + RIM_LIP_H)
        .circle(AUGER_OD / 2)
        .circle(AUGER_OD / 2 - 2.0)
        .extrude(20.0)
    )


# ============================================================================
# Assemblies
# ============================================================================

def assembly(open: bool = False) -> cq.Assembly:
    asm = cq.Assembly()
    # Lower (driver) disc at Z = 0
    asm.add(lower_disc(open=open), name="driver_disc",
            color=cq.Color(0.78, 0.70, 0.95))
    # Upper (channel-side) disc stacked on top
    asm.add(upper_disc().translate((0, 0, DISC_T)),
            name="channel_disc", color=cq.Color(0.78, 0.70, 0.95))
    # M3 nut sits in the captive pocket on the bottom of the driver disc
    asm.add(m3_nut().translate((0, 0, NUT_POCKET_DEPTH - M3_NUT_H)),
            name="m3_nut", color=cq.Color(0.30, 0.30, 0.30))
    # M3 screw enters from above through the channel-disc counterbore;
    # head sits in the counterbore (top face of channel disc)
    screw_z0 = 2 * DISC_T - M3_SHANK_LEN + M3_HEAD_H + 0.5
    asm.add(m3_screw().translate((0, 0, screw_z0)),
            name="m3_screw", color=cq.Color(0.30, 0.30, 0.30))
    asm.add(auger_stub(), name="auger_stub_REF",
            color=cq.Color(0.55, 0.55, 0.55))
    return asm


def exploded_assembly() -> cq.Assembly:
    """Pulls the parts apart along Z so the order of assembly is obvious."""
    asm = cq.Assembly()
    Z0 = 0.0
    Z1 = DISC_T + 8.0       # gap 1: lift channel disc 8 mm above driver
    Zscrew = Z1 + DISC_T + 12.0
    Znut = Z0 - 12.0

    asm.add(lower_disc(open=False).translate((0, 0, Z0)),
            name="1_driver_disc", color=cq.Color(0.78, 0.70, 0.95))
    asm.add(upper_disc().translate((0, 0, Z1)),
            name="2_channel_disc", color=cq.Color(0.78, 0.70, 0.95))
    asm.add(m3_screw().translate((0, 0, Zscrew)),
            name="3_m3_screw", color=cq.Color(0.30, 0.30, 0.30))
    asm.add(m3_nut().translate((0, 0, Znut)),
            name="4_m3_nut", color=cq.Color(0.30, 0.30, 0.30))
    asm.add(auger_stub().translate((0, 0, 18.0)),
            name="auger_stub_REF", color=cq.Color(0.55, 0.55, 0.55))
    return asm


# ============================================================================
# Export
# ============================================================================

def _save_svg(compound, name, vec):
    svg = cq.exporters.svg.getSVG(
        compound,
        opts={
            "projectionDir": vec,
            "showAxes": False,
            "strokeColor": (40, 40, 40),
            "hiddenColor": (180, 180, 180),
            "showHidden": False,
            "width": 800,
            "height": 800,
            "marginLeft": 40,
            "marginTop": 40,
        },
    )
    (RENDER / f"{name}.svg").write_text(svg)
    print(f"wrote renders/{name}.svg")


def export_all() -> None:
    asm_closed = assembly(open=False)
    step_path = OUT / "sealing_cap_twist_shutter.step"
    asm_closed.save(str(step_path))
    print(f"wrote {step_path}")

    cq.exporters.export(upper_disc(), str(STL / "channel_disc.stl"))
    cq.exporters.export(lower_disc(open=False), str(STL / "driver_disc.stl"))
    print(f"wrote {STL}/channel_disc.stl, driver_disc.stl")

    views = {
        "iso": (1, -1, 0.8),
        "front": (0, -1, 0),
        "top": (0, 0, 1),
        "side": (1, 0, 0),
    }
    for name, vec in views.items():
        _save_svg(asm_closed.toCompound(),
                  f"sealing_cap_twist_shutter_{name}", vec)

    _save_svg(exploded_assembly().toCompound(),
              "sealing_cap_twist_shutter_exploded", (1, -1, 0.5))


if __name__ == "__main__":
    export_all()
