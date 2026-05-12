#!/usr/bin/env python3
"""Shared physical-world frame for the powder-dosing alternatives (A–H).

Per @sgbaird-yolo on PR #13: the prior Pillow-only animation had
spatial inconsistencies because each tile's pixel anchors were hard
coded. This module defines **a single shared world frame in
millimetres** plus **a single projection** from world (x, z) mm to
pixel (px, py). Every concept's CAD scene
(:mod:`scripts.cad_scenes`) and every per-concept animator frame
(:mod:`scripts.animate_dispensing_cad`) consume this module — so the
bed plane, vial mouth, gantry rail and mechanism home column line up
across all eight tiles **by construction**, not by manual numeric
matching.

Conventions
-----------
* World units are millimetres.
* World axes match the 3018-Pro V2: ``+x`` is gantry-travel (left→right
  on side view), ``+z`` is up. ``y`` is into the page on side view.
* Side-view projection is the (x, z) plane.
* Pixel origin is top-left (Pillow / matplotlib image convention) so
  the projector negates ``z`` to make up→up.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorldFrame:
    """Shared world-frame anchors. All values in millimetres unless noted."""

    # ----- 3018-Pro V2 working envelope (side-view bounds, mm) -------
    work_xmin: float = -160.0
    work_xmax: float = 160.0
    work_zmin: float = 0.0
    work_zmax: float = 110.0

    # ----- Bed plane (top of T-slot bed) -----------------------------
    bed_z: float = 0.0
    bed_thickness: float = 6.0

    # ----- Gantry rail (mechanical top of the gantry, side view) -----
    # Y-axis steel bar carrying the spindle clamp; sets the upper
    # bound of the mechanism travel.
    gantry_rail_z: float = 95.0
    gantry_rail_h: float = 6.0

    # ----- Mechanism rest column ("home" pose, gantry parked) --------
    mech_home_x: float = -45.0

    # ----- Vial (15 mm OD scintillation vial on the bed) -------------
    vial_x: float = 60.0
    vial_od: float = 15.0
    vial_h: float = 45.0
    # Mouth z (top of vial) = bed_z + vial_h.

    @property
    def vial_top_z(self) -> float:
        return self.bed_z + self.vial_h

    # ----- Spindle-clamp grip diameter on the V2 (used to size the
    # boss on every concept that mounts to the spindle).
    spindle_clamp_d: float = 43.0


WORLD = WorldFrame()


# ---------------------------------------------------------------------------
# Single shared (x, z) mm -> (px, py) pixel projector
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SideProjector:
    """Project world (x_mm, z_mm) -> pixel (px, py) for side views.

    A single ``SideProjector`` instance is used by *every* per-concept
    renderer so the bed-line, gantry rail, vial mouth, and mechanism
    home column land on identical pixel rows/columns across the
    composite tile.
    """

    frame_w_px: int = 480
    frame_h_px: int = 360
    margin_px: int = 18
    # World bounds projected into the frame (slightly tighter than the
    # full machine envelope so labels have a margin).
    x_lo_mm: float = -85.0
    x_hi_mm: float = 95.0
    z_lo_mm: float = -8.0
    z_hi_mm: float = 108.0

    # Header / footer reserved bands (pixels) so the bed Y is still the
    # same across every tile when title + phase label are added.
    title_h_px: int = 28
    footer_h_px: int = 20

    def _draw_box(self) -> tuple[int, int, int, int]:
        x0 = self.margin_px
        x1 = self.frame_w_px - self.margin_px
        y0 = self.title_h_px + 4
        y1 = self.frame_h_px - self.footer_h_px - 4
        return x0, y0, x1, y1

    def project(self, x_mm: float, z_mm: float) -> tuple[float, float]:
        x0, y0, x1, y1 = self._draw_box()
        u = (x_mm - self.x_lo_mm) / max(self.x_hi_mm - self.x_lo_mm, 1e-9)
        v = (z_mm - self.z_lo_mm) / max(self.z_hi_mm - self.z_lo_mm, 1e-9)
        px = x0 + u * (x1 - x0)
        py = y1 - v * (y1 - y0)  # flip: world +z up → pixel up
        return px, py

    def project_box(
        self,
        x_mm: float,
        z_mm: float,
        dx_mm: float,
        dz_mm: float,
    ) -> tuple[float, float, float, float]:
        """Project a (x, z, dx, dz) world AABB to pixel (x0, y0, x1, y1)."""
        p0x, p0y = self.project(x_mm, z_mm + dz_mm)
        p1x, p1y = self.project(x_mm + dx_mm, z_mm)
        return p0x, p0y, p1x, p1y

    def mm_per_px(self) -> float:
        x0, _, x1, _ = self._draw_box()
        return (self.x_hi_mm - self.x_lo_mm) / max(x1 - x0, 1)


PROJ = SideProjector()


if __name__ == "__main__":
    print(f"WORLD = {WORLD!r}")
    print(f"PROJ  = {PROJ!r}")
    # Sanity-print a few key anchors so the user can see they
    # really do come out of one transform.
    for label, (x, z) in [
        ("bed-center      ", (0.0, WORLD.bed_z)),
        ("gantry-rail-home", (WORLD.mech_home_x, WORLD.gantry_rail_z)),
        ("vial-mouth      ", (WORLD.vial_x, WORLD.vial_top_z)),
        ("vial-bottom     ", (WORLD.vial_x, WORLD.bed_z)),
    ]:
        px, py = PROJ.project(x, z)
        print(f"  {label}  ({x:+6.1f}, {z:+6.1f}) mm  ->  ({px:6.1f}, {py:6.1f}) px")
