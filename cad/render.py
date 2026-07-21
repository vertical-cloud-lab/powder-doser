"""Render the parametric CAD model to SVG views of the actual 3D geometry.

Where ``scripts/generate_figures.py`` draws hand-laid-out *schematic* figures
that explain the design intent, this module produces *honest renders* of the
geometry returned by :mod:`cad.excavator` -- i.e.\\ what the part will
actually look like when it comes off the FDM printer. Each part gets a small
vector SVG (hidden-line removed) under ``docs/figures/cad/``; the full
assembly gets one extra render so the trough/arms/pin relationship is
visible at a glance.

Run from the repo root::

    python -m cad.render

Outputs land under ``docs/figures/cad/`` (committed alongside the schematic
figures so they appear in the GitHub preview without requiring a full CAD
toolchain on the reader's machine).

Implementation notes:

* CadQuery's built-in SVG exporter is used (``cq.exporters.export(... ,
  exportType='SVG', opt=...)``). This is a vector projection with hidden-
  line removal; no raster renderer or X server is required.

* The model uses CadQuery's +Y as "world up" (open top of the trough) and
  +Z as the trough's longitudinal pin axis L. The default isometric
  projection direction sits the camera on the +X / +Y / +Z octant so the
  open ladle interior is visible.

* The assembly is rendered by collapsing it to a single ``Compound`` via
  ``asm.toCompound()``; this loses per-part colour but keeps geometry,
  which is the point of a "what does the print look like" view.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import cadquery as cq

from .excavator import (
    ExcavatorParams,
    build_arm,
    build_assembly,
    build_cam_ramp,
    build_pin,
    build_slot_board,
    build_strike_off_bar,
    build_trough,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
RENDER_DIR = REPO_ROOT / "docs" / "figures" / "cad"

# Isometric viewpoint: camera on +X / +Y / +Z octant, looking back toward
# the origin. CadQuery's ``projectionDir`` is the camera's look-at direction
# (from camera to scene), so a vector with all-negative components puts the
# camera in the all-positive octant. With the trough's open top facing +Y
# this exposes the ladle interior, end caps, and rim lips simultaneously.
_ISO_DIR = (-0.7, -1.0, -0.6)

# Shared SVG exporter options. Picked so every part renders into the same
# isometric viewpoint with hidden-line dashes turned on, which is what a
# reader expects from a "CAD render" -- a clean orthographic-style line
# drawing rather than a shaded raster.
_BASE_OPT: dict[str, Any] = {
    "width": 720,
    "height": 540,
    "marginLeft": 20,
    "marginTop": 20,
    "showAxes": False,
    "projectionDir": _ISO_DIR,
    "strokeWidth": 0.4,
    "strokeColor": (40, 40, 40),
    "hiddenColor": (180, 180, 180),
    "showHidden": True,
}


def _render(part: cq.Workplane | cq.Shape, stem: str, **opt_overrides: Any) -> Path:
    """Render a single part to ``RENDER_DIR / f"{stem}.svg"`` and return the path."""
    opt = {**_BASE_OPT, **opt_overrides}
    out = RENDER_DIR / f"{stem}.svg"
    cq.exporters.export(part, str(out), exportType="SVG", opt=opt)
    return out


def main() -> None:
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    p = ExcavatorParams()

    # Per-part renders. Order them so the printable parts come first
    # (they are the ones a reader will actually slice and print).
    parts: dict[str, Callable[[ExcavatorParams], Any]] = {
        "trough":         build_trough,
        "arm":            build_arm,
        "pin":            build_pin,
        "strike_off_bar": build_strike_off_bar,
        "cam_ramp":       build_cam_ramp,
        "slot_board":     build_slot_board,
    }
    for name, fn in parts.items():
        out = _render(fn(p), name)
        print(f"wrote {out.relative_to(REPO_ROOT)}")

    # Full assembly. We render three views so the arm / pin / trough
    # relationship is unambiguous: an isometric (default), an end view
    # (looking along the pin axis -- shows the half-cylinder cross-section
    # and how the arms grip the end caps), and a side view (perpendicular
    # to the pin axis -- shows the full length L and both arms).
    asm = build_assembly(p)
    comp = asm.toCompound()
    for view, proj in (
        ("assembly",          _ISO_DIR),         # iso
        ("assembly-end",      (0.0, 0.0, -1.0)), # along the pin axis
        ("assembly-side",     (1.0, 0.0, 0.0)),  # perpendicular to pin axis
    ):
        out = _render(comp, view, width=900, height=600, projectionDir=proj)
        print(f"wrote {out.relative_to(REPO_ROOT)}")


if __name__ == "__main__":  # pragma: no cover
    main()
