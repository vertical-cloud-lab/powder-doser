"""
Parametric CadQuery model — Twist-Shutter Sealing Cap (Concept §2.1 of
design/cap-brainstorming.md).

Two coaxial discs stacked face-to-face, each with a sector-shaped slot.
Rotating the lower (driver) disc 60° relative to the upper (channel-side)
disc lines the two slots up and opens the Ø3 mm dispense path.

  +Z = up
  Z = 0 at the bottom of the auger-channel exit (top of upper disc)
  All dimensions in millimetres.

Run:
    python cad_model.py
which writes ./renders/*.svg, ./stl/*.stl, ./sealing_cap_twist_shutter.step.
"""

from __future__ import annotations

from pathlib import Path

import cadquery as cq

OUT = Path(__file__).parent
RENDER = OUT / "renders"
STL = OUT / "stl"
RENDER.mkdir(exist_ok=True)
STL.mkdir(exist_ok=True)


# ============================================================================
# Geometry — single source of truth (mirrored in sketch_2d.py).
# ============================================================================

# --- Auger / channel interface (PR-#16 archimedes-auger.scad v4) -----------
AUGER_OD = 25.0          # auger outer cylinder
EXIT_HOLE_D = 3.0        # auger exit hole

# --- Cap envelope ----------------------------------------------------------
CAP_OD = 36.0            # outer diameter of both discs
DISC_T = 4.0             # thickness of each disc
PIVOT_D = 4.0            # central pivot pin (M3 clearance + slop)
RIM_LIP_H = 3.0          # snap-on lip that grips the auger Ø25 OD
RIM_LIP_T = 1.6          # wall thickness of that lip

# --- Slot geometry (sector through both discs) -----------------------------
# A sector centred at the pivot, sweeping SLOT_ANGLE, with inner and outer
# radii. EXIT_HOLE_D worth of area must clear when slots align.
SLOT_INNER_R = 4.0
SLOT_OUTER_R = 8.0
SLOT_ANGLE = 60.0        # sweep in degrees

# Twist between closed (slots 180° apart on the OD-side) and open (aligned).
TWIST_OPEN_DEG = 60.0

# --- Driver-disc actuation tab ---------------------------------------------
TAB_W = 6.0
TAB_L = 14.0             # protrudes radially past CAP_OD
TAB_T = 3.0


# ============================================================================
# Parts
# ============================================================================

def _disc_with_slot(angle_offset: float, with_lip: bool) -> cq.Workplane:
    """A flat disc with a sector slot. angle_offset rotates the slot.

    The lip variant (`with_lip=True`) is the upper, channel-side disc and
    has an upward-facing snap rim that grips the auger OD."""
    disc = (
        cq.Workplane("XY")
        .circle(CAP_OD / 2)
        .extrude(DISC_T)
    )

    # Central pivot bore
    disc = disc.faces(">Z").workplane().hole(PIVOT_D)

    # Sector slot — build as a thin pie wedge minus an inner pie wedge,
    # rotated by angle_offset.
    half = SLOT_ANGLE / 2.0
    pts_outer = [(0, 0)]
    pts_inner = [(0, 0)]
    import math
    steps = 24
    for i in range(steps + 1):
        a = math.radians(-half + i * SLOT_ANGLE / steps)
        pts_outer.append((SLOT_OUTER_R * math.cos(a), SLOT_OUTER_R * math.sin(a)))
        pts_inner.append((SLOT_INNER_R * math.cos(a), SLOT_INNER_R * math.sin(a)))
    pts_outer.append((0, 0))
    pts_inner.append((0, 0))

    sector_outer = cq.Workplane("XY").polyline(pts_outer).close().extrude(DISC_T)
    sector_inner = cq.Workplane("XY").polyline(pts_inner).close().extrude(DISC_T)
    slot = sector_outer.cut(sector_inner)
    slot = slot.rotate((0, 0, 0), (0, 0, 1), angle_offset)

    disc = disc.cut(slot)

    if with_lip:
        # Snap lip on top to grip the auger OD
        lip_outer_r = AUGER_OD / 2 + RIM_LIP_T
        lip = (
            cq.Workplane("XY")
            .workplane(offset=DISC_T)
            .circle(lip_outer_r)
            .circle(AUGER_OD / 2)
            .extrude(RIM_LIP_H)
        )
        disc = disc.union(lip)

    return disc


def upper_disc() -> cq.Workplane:
    """Channel-side disc; slot at 0° (reference)."""
    return _disc_with_slot(angle_offset=0.0, with_lip=True)


def lower_disc(open: bool = False) -> cq.Workplane:
    """Driver disc; slot rotated 180° (closed) or 180° - 60° (open)."""
    angle = 180.0 - TWIST_OPEN_DEG if open else 180.0
    disc = _disc_with_slot(angle_offset=angle, with_lip=False)

    # Actuation tab — radial paddle the dispense head's cam can push
    tab = (
        cq.Workplane("XY")
        .box(TAB_L, TAB_W, TAB_T, centered=(False, True, False))
        .translate((CAP_OD / 2 - 1.0, 0, 0))
    )
    # Tab also rotates with the disc
    tab = tab.rotate((0, 0, 0), (0, 0, 1), angle)
    return disc.union(tab)


def auger_stub() -> cq.Workplane:
    """A short visualization stub of the PR-#16 auger OD — not printed."""
    return (
        cq.Workplane("XY")
        .workplane(offset=DISC_T + RIM_LIP_H)
        .circle(AUGER_OD / 2)
        .circle(AUGER_OD / 2 - 2.0)  # 2 mm wall, matches auger v4
        .extrude(20.0)
    )


# ============================================================================
# Assembly + export
# ============================================================================

def assembly(open: bool = False) -> cq.Assembly:
    asm = cq.Assembly()
    # Lower (driver) disc at Z = 0
    asm.add(lower_disc(open=open), name="driver_disc",
            color=cq.Color(0.78, 0.70, 0.95))
    # Upper (channel-side) disc stacked on top — translate up by DISC_T
    asm.add(upper_disc().translate((0, 0, DISC_T)),
            name="channel_disc", color=cq.Color(0.78, 0.70, 0.95))
    # Auger stub for context
    asm.add(auger_stub(), name="auger_stub_REF",
            color=cq.Color(0.55, 0.55, 0.55))
    return asm


def export_all() -> None:
    asm_closed = assembly(open=False)
    asm_open = assembly(open=True)

    # STEP — the closed configuration is canonical
    step_path = OUT / "sealing_cap_twist_shutter.step"
    asm_closed.save(str(step_path))
    print(f"wrote {step_path}")

    # Per-part STLs
    cq.exporters.export(upper_disc(), str(STL / "channel_disc.stl"))
    cq.exporters.export(lower_disc(open=False), str(STL / "driver_disc.stl"))
    print(f"wrote {STL}/channel_disc.stl, driver_disc.stl")

    # Four-view SVGs of the closed assembly
    compound = asm_closed.toCompound()
    views = {
        "iso": (1, -1, 0.8),
        "front": (0, -1, 0),
        "top": (0, 0, 1),
        "side": (1, 0, 0),
    }
    for name, vec in views.items():
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
        (RENDER / f"sealing_cap_twist_shutter_{name}.svg").write_text(svg)
        print(f"wrote renders/sealing_cap_twist_shutter_{name}.svg")


if __name__ == "__main__":
    export_all()
