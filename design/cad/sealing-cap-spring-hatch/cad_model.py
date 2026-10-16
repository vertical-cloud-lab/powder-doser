"""
Parametric CadQuery model — Spring-Hatch Sealing Cap (Concept §2.2 of
design/cap-brainstorming.md).

REVISION addressing PR #37 review (@swcharles):
  > The spring-hatch design doesn't make a lot of sense to me,
  > particularly when looking at the stl files. How are they supposed
  > to fit together?

Resolution: the cap is genuinely a SINGLE PRINTED PART. The base, the
living-hinge web, the flap, and the cam tab are all one piece of PETG —
that is the whole point of a flexure design. The previous draft split
them into two STLs only for visual inspection and never explained how
they bonded; this revision exports `spring_hatch_unified.stl` as the
real print file, plus an exploded view that makes the flap → hinge →
base relationship obvious.

Coordinate frame:
  +Z = up (towards the auger). Z = 0 at top of cap base.
  +X is the hinge side; the flap closes by swinging in the −X direction.
  All dimensions in millimetres.

Run:
    python cad_model.py
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

# --- Cap base --------------------------------------------------------------
BASE_W = 36.0           # square footprint side (was a disc; square gives a
                         # flat ledge for the hinge)
BASE_T = 6.0
COLLAR_H = 8.0
COLLAR_WALL = 1.6
SEAL_BORE_D = 6.0
SEAL_BORE_DEPTH = 2.0

# --- Flap window -----------------------------------------------------------
FLAP_OD = 18.0          # the flap is a Ø18 disc
FLAP_T = 2.5
FLAP_CLEAR = 0.4        # radial clearance between flap and window edge
WINDOW_OFFSET_X = -2.0  # the flap (and window) is centred slightly −X of the
                         # auger axis so the hinge webs sit out of the powder
                         # column
FLAP_BOTTOM_Z = 0.5     # bottom of the flap lives this many mm above the
                         # bottom face of the base — i.e. flap top face is at
                         # FLAP_BOTTOM_Z + FLAP_T = 3.0 mm
FLAP_TOP_Z = FLAP_BOTTOM_Z + FLAP_T

# --- Living-hinge web ------------------------------------------------------
# Two thin straps of PETG bridging the +X edge of the flap to the +X edge
# of the base window. They behave as a torsion spring; the bend axis is
# the line where they meet the flap.
HINGE_WEB_T = 0.6
HINGE_WEB_W = 4.0
HINGE_WEB_GAP_Y = 7.0   # centre-to-centre between the two webs
HINGE_WEB_LEN = 3.0     # X length of the bend region

# --- Cam tab ---------------------------------------------------------------
# A downward-pointing tab on the −X edge of the flap. The dispense head's
# stationary cam pin pushes this tab in +X, lifting the flap.
CAM_TAB_W = 5.0
CAM_TAB_H = 4.0         # protrudes below FLAP_BOTTOM_Z by this much
CAM_TAB_L = 4.0


# ============================================================================
# Geometry helpers
# ============================================================================

def _flap_centre_x() -> float:
    return WINDOW_OFFSET_X


def _hinge_root_x() -> float:
    """The +X edge of the flap (where it meets the hinge web)."""
    return _flap_centre_x() + FLAP_OD / 2


def _ledge_root_x() -> float:
    """The +X edge of the base window (where the other end of the web bonds)."""
    return _hinge_root_x() + HINGE_WEB_LEN


# ============================================================================
# Single-piece printed part — base + hinge webs + flap + cam tab fused
# ============================================================================

def unified() -> cq.Workplane:
    """Return the single solid that you actually print.

    Construction is additive: start with the base solid, add the hinge
    webs, add the flap, add the cam tab. The window in the base
    (through-hole that lets powder past the flap when open) is cut
    everywhere except where the flap, hinge webs, and cam tab live.
    """
    # ------------------------------------------------------------------
    # 1. Base block + snap collar
    # ------------------------------------------------------------------
    body = cq.Workplane("XY").box(BASE_W, BASE_W, BASE_T,
                                   centered=(True, True, False))

    collar = (
        cq.Workplane("XY")
        .workplane(offset=BASE_T)
        .circle(AUGER_OD / 2 + COLLAR_WALL)
        .circle(AUGER_OD / 2)
        .extrude(COLLAR_H)
    )
    body = body.union(collar)

    # Seal funnel into the auger exit on the +Z face
    body = (
        body.faces(">Z")
        .workplane(invert=True)
        .moveTo(0, 0)
        .hole(SEAL_BORE_D, SEAL_BORE_DEPTH)
    )

    # ------------------------------------------------------------------
    # 2. Cut the flap window straight through the base
    # ------------------------------------------------------------------
    # The window is the Ø(FLAP_OD + 2*FLAP_CLEAR) bore where the flap
    # lives (and pivots out of, when open).
    window = (
        cq.Workplane("XY")
        .moveTo(_flap_centre_x(), 0)
        .circle(FLAP_OD / 2 + FLAP_CLEAR)
        .extrude(BASE_T + 0.01)
    )
    body = body.cut(window)

    # ------------------------------------------------------------------
    # 3. Add the flap (sits inside the window when closed)
    # ------------------------------------------------------------------
    flap = (
        cq.Workplane("XY")
        .workplane(offset=FLAP_BOTTOM_Z)
        .moveTo(_flap_centre_x(), 0)
        .circle(FLAP_OD / 2)
        .extrude(FLAP_T)
    )
    body = body.union(flap)

    # ------------------------------------------------------------------
    # 4. Add the two living-hinge webs that fuse the flap to the base
    # ------------------------------------------------------------------
    # Each web is a thin strap at the flap's top-face level, bridging
    # x = hinge_root_x → ledge_root_x, centred at ±HINGE_WEB_GAP_Y/2
    # along Y.
    for y_centre in (-HINGE_WEB_GAP_Y / 2, HINGE_WEB_GAP_Y / 2):
        web = (
            cq.Workplane("XY")
            .workplane(offset=FLAP_TOP_Z - HINGE_WEB_T)
            .moveTo(_hinge_root_x(), y_centre - HINGE_WEB_W / 2)
            .rect(HINGE_WEB_LEN, HINGE_WEB_W, centered=False)
            .extrude(HINGE_WEB_T)
        )
        body = body.union(web)

    # ------------------------------------------------------------------
    # 5. Cam tab on the −X side of the flap, pointing downward
    # ------------------------------------------------------------------
    cam = (
        cq.Workplane("XY")
        .workplane(offset=FLAP_BOTTOM_Z - CAM_TAB_H)
        .moveTo(_flap_centre_x() - FLAP_OD / 2 - CAM_TAB_L,
                -CAM_TAB_W / 2)
        .rect(CAM_TAB_L, CAM_TAB_W, centered=False)
        .extrude(CAM_TAB_H + FLAP_T + 0.5)
    )
    body = body.union(cam)

    return body


# ============================================================================
# Reference (NON-PRINT) sub-pieces — for visualization only
# ============================================================================

def reference_cap_base() -> cq.Workplane:
    """The base + collar minus the flap window — what's 'left over' if you
    pretend the flap+hinge isn't there. Visual aid only; do not print."""
    body = cq.Workplane("XY").box(BASE_W, BASE_W, BASE_T,
                                   centered=(True, True, False))
    collar = (
        cq.Workplane("XY")
        .workplane(offset=BASE_T)
        .circle(AUGER_OD / 2 + COLLAR_WALL)
        .circle(AUGER_OD / 2)
        .extrude(COLLAR_H)
    )
    body = body.union(collar)
    body = (
        body.faces(">Z")
        .workplane(invert=True)
        .moveTo(0, 0)
        .hole(SEAL_BORE_D, SEAL_BORE_DEPTH)
    )
    window = (
        cq.Workplane("XY")
        .moveTo(_flap_centre_x(), 0)
        .circle(FLAP_OD / 2 + FLAP_CLEAR)
        .extrude(BASE_T + 0.01)
    )
    return body.cut(window)


def reference_flap() -> cq.Workplane:
    """Flap disc + cam tab as a separate visual piece. Do not print this
    on its own — the real print is `unified()`."""
    flap = (
        cq.Workplane("XY")
        .moveTo(_flap_centre_x(), 0)
        .circle(FLAP_OD / 2)
        .extrude(FLAP_T)
    )
    cam = (
        cq.Workplane("XY")
        .workplane(offset=-CAM_TAB_H)
        .moveTo(_flap_centre_x() - FLAP_OD / 2 - CAM_TAB_L,
                -CAM_TAB_W / 2)
        .rect(CAM_TAB_L, CAM_TAB_W, centered=False)
        .extrude(CAM_TAB_H + FLAP_T)
    )
    return flap.union(cam)


# ============================================================================
# Auger reference stub
# ============================================================================

def auger_stub() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .workplane(offset=BASE_T + COLLAR_H)
        .circle(AUGER_OD / 2)
        .circle(AUGER_OD / 2 - 2.0)
        .extrude(20.0)
    )


# ============================================================================
# Assemblies
# ============================================================================

def assembly() -> cq.Assembly:
    """Closed configuration — the print as it sits on the bench."""
    asm = cq.Assembly()
    asm.add(unified(), name="cap_unified",
            color=cq.Color(0.78, 0.70, 0.95))
    asm.add(auger_stub(), name="auger_stub_REF",
            color=cq.Color(0.55, 0.55, 0.55))
    return asm


def exploded_assembly() -> cq.Assembly:
    """Exploded view — pulls the reference flap out below the base so the
    interface (window + hinge ledge) is obvious.

    Note: this is a *visual* explode using the two reference pieces, not
    of the unified part — you can't pull a single solid apart!
    """
    asm = cq.Assembly()
    asm.add(reference_cap_base(), name="cap_base (printed as part of unified)",
            color=cq.Color(0.78, 0.70, 0.95))
    asm.add(reference_flap().translate((0, 0, -15.0)), name="flap (printed as part of unified)",
            color=cq.Color(0.55, 0.85, 0.55))
    # Two hinge-web indicators (small green sticks) showing where the
    # webs bridge between the two pieces in the unified print
    for y in (-HINGE_WEB_GAP_Y / 2, HINGE_WEB_GAP_Y / 2):
        web_indicator = (
            cq.Workplane("XY")
            .workplane(offset=(FLAP_TOP_Z - 15.0) - HINGE_WEB_T / 2)
            .moveTo(_hinge_root_x(), y - HINGE_WEB_W / 2)
            .rect(HINGE_WEB_LEN, HINGE_WEB_W, centered=False)
            .extrude(15.0 + HINGE_WEB_T)
        )
        asm.add(web_indicator,
                name=f"hinge_web_y={y:+.1f} (the PETG flexure)",
                color=cq.Color(0.20, 0.55, 0.20))
    asm.add(auger_stub(), name="auger_stub_REF",
            color=cq.Color(0.55, 0.55, 0.55))
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
    asm = assembly()
    step_path = OUT / "sealing_cap_spring_hatch.step"
    asm.save(str(step_path))
    print(f"wrote {step_path}")

    # The single PRINT file
    cq.exporters.export(unified(), str(STL / "spring_hatch_unified.stl"))
    print(f"wrote {STL}/spring_hatch_unified.stl  [PRINT THIS]")
    # Reference pieces for visual inspection only
    cq.exporters.export(reference_cap_base(),
                        str(STL / "reference_cap_base.stl"))
    cq.exporters.export(reference_flap(), str(STL / "reference_flap.stl"))
    print(f"wrote {STL}/reference_*.stl  [visual aids only — do not print]")

    views = {
        "iso": (1, -1, 0.8),
        "front": (0, -1, 0),
        "top": (0, 0, 1),
        "side": (1, 0, 0),
    }
    for name, vec in views.items():
        _save_svg(asm.toCompound(), f"sealing_cap_spring_hatch_{name}", vec)

    # Exploded view (iso)
    _save_svg(exploded_assembly().toCompound(),
              "sealing_cap_spring_hatch_exploded", (1, -1, 0.6))


if __name__ == "__main__":
    export_all()
