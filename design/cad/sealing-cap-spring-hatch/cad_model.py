"""
Parametric CadQuery model — Spring-Hatch Sealing Cap (Concept §2.2 of
design/cap-brainstorming.md).

A printed flexure hinge holds a Ø22 flap closed against the auger exit
face. The flap's outboard edge carries a 4-mm-tall cam tab that the
dispense head's stationary cam pin pushes radially when the cartridge
seats, swinging the flap clear of the Ø3 mm exit. Pulling the cartridge
out lets the flexure return the flap to closed.

Coordinate frame:
  +Z = up (towards the auger), Z = 0 at top of cap base.
  Hinge axis is along +Y. Flap swings about that axis.
  All dimensions in millimetres.
"""

from __future__ import annotations

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

# --- Cap base --------------------------------------------------------------
BASE_OD = 32.0           # outer diameter of the cap collar
BASE_T = 5.0             # base thickness (carries the seal face)
SEAL_BORE_D = 6.0        # local funnel just under the auger Ø3 exit
SEAL_BORE_DEPTH = 2.0
COLLAR_H = 8.0           # snap-collar height above the base, hugs auger OD
COLLAR_WALL = 1.6

# --- Flap / hinge ----------------------------------------------------------
FLAP_OD = 22.0
FLAP_T = 2.5
FLAP_OFFSET_X = 1.0      # centred over EXIT_HOLE; offset to clear hinge
HINGE_FLEXURE_T = 0.6    # PETG living-hinge thickness — print-tunable
HINGE_FLEXURE_W = 8.0
HINGE_GAP = 0.4          # gap between flap edge and base edge at hinge

# --- Cam tab (the part the dispense head pushes) ---------------------------
CAM_TAB_W = 5.0
CAM_TAB_H = 4.0          # protrudes BELOW the flap, into mechanism space
CAM_TAB_L = 6.0          # along radial direction


def cap_base() -> cq.Workplane:
    """Base disc + snap collar + local funnel under the auger exit."""
    base = cq.Workplane("XY").circle(BASE_OD / 2).extrude(BASE_T)
    # Snap collar gripping the auger OD on top
    collar = (
        cq.Workplane("XY")
        .workplane(offset=BASE_T)
        .circle(AUGER_OD / 2 + COLLAR_WALL)
        .circle(AUGER_OD / 2)
        .extrude(COLLAR_H)
    )
    base = base.union(collar)
    # Local Ø6 × 2 mm recess under the Ø3 exit so cap-closed face is the
    # *flap*, not the auger's printed exit (which is rough).
    base = (
        base.faces(">Z")
        .workplane(invert=True)
        .moveTo(0, 0)
        .hole(SEAL_BORE_D, SEAL_BORE_DEPTH)
    )
    # Cut a cavity on the −X side of the base where the flap parks when open
    cavity = (
        cq.Workplane("XY")
        .workplane(offset=BASE_T - FLAP_T - 0.4)
        .moveTo(-(FLAP_OD / 2 + 2), 0)
        .rect(FLAP_OD + 4, FLAP_OD + 4, centered=True)
        .extrude(FLAP_T + 0.4)
    )
    # Don't cut all the way through — leave a thin floor for stiffness
    base = base.cut(cavity)
    return base


def flap() -> cq.Workplane:
    """Flap + integral living-hinge tab + cam tab, in closed position."""
    f = (
        cq.Workplane("XY")
        .moveTo(FLAP_OFFSET_X, 0)
        .circle(FLAP_OD / 2)
        .extrude(FLAP_T)
    )
    # Living hinge — thin web extending in +X from the flap edge
    hinge_x_start = FLAP_OFFSET_X + FLAP_OD / 2
    hinge = (
        cq.Workplane("XY")
        .moveTo(hinge_x_start, -HINGE_FLEXURE_W / 2)
        .rect(2.0, HINGE_FLEXURE_W, centered=False)
        .extrude(HINGE_FLEXURE_T)
        .translate((0, 0, FLAP_T - HINGE_FLEXURE_T))
    )
    # Anchor — small block at the far end of the hinge that bonds to base
    anchor = (
        cq.Workplane("XY")
        .moveTo(hinge_x_start + 2.0, -HINGE_FLEXURE_W / 2 - 1.0)
        .rect(3.0, HINGE_FLEXURE_W + 2.0, centered=False)
        .extrude(FLAP_T)
    )
    # Cam tab — points DOWN (−Z) from the flap on the −X edge
    cam = (
        cq.Workplane("XY")
        .moveTo(FLAP_OFFSET_X - FLAP_OD / 2 - CAM_TAB_L, -CAM_TAB_W / 2)
        .rect(CAM_TAB_L, CAM_TAB_W, centered=False)
        .extrude(-CAM_TAB_H)
    )
    # Bridge between flap edge and cam tab so cam motion lifts the flap
    bridge = (
        cq.Workplane("XY")
        .moveTo(FLAP_OFFSET_X - FLAP_OD / 2 - CAM_TAB_L, -CAM_TAB_W / 2)
        .rect(CAM_TAB_L, CAM_TAB_W, centered=False)
        .extrude(FLAP_T)
    )
    return f.union(hinge).union(anchor).union(cam).union(bridge)


def auger_stub() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .workplane(offset=BASE_T + COLLAR_H)
        .circle(AUGER_OD / 2)
        .circle(AUGER_OD / 2 - 2.0)
        .extrude(20.0)
    )


def assembly() -> cq.Assembly:
    asm = cq.Assembly()
    # Flap closed position: just below the seal bore, on top of base recess
    flap_z = BASE_T - FLAP_T - 0.2
    asm.add(cap_base(), name="cap_base",
            color=cq.Color(0.78, 0.70, 0.95))
    asm.add(flap().translate((0, 0, flap_z)), name="flap",
            color=cq.Color(0.55, 0.85, 0.55))
    asm.add(auger_stub(), name="auger_stub_REF",
            color=cq.Color(0.55, 0.55, 0.55))
    return asm


def export_all() -> None:
    asm = assembly()
    step_path = OUT / "sealing_cap_spring_hatch.step"
    asm.save(str(step_path))
    print(f"wrote {step_path}")

    cq.exporters.export(cap_base(), str(STL / "cap_base.stl"))
    cq.exporters.export(flap(), str(STL / "flap.stl"))
    print(f"wrote {STL}/cap_base.stl, flap.stl")

    compound = asm.toCompound()
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
        (RENDER / f"sealing_cap_spring_hatch_{name}.svg").write_text(svg)
        print(f"wrote renders/sealing_cap_spring_hatch_{name}.svg")


if __name__ == "__main__":
    export_all()
