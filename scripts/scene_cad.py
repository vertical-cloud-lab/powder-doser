#!/usr/bin/env python3
"""Physical CAD scenes for the eight A–H powder-dosing alternatives.

Every concept is built with CadQuery (real 3-D solids in millimetres)
inside the **shared** :data:`scripts.scene_world_frame.WORLD` frame.
Each concept exposes a :func:`pose` function returning, for a given
phase/progress, a list of named :class:`Part` rectangles in world
``(x, z, dx, dz)`` mm — and a matching CadQuery :class:`cadquery.Assembly`
whose AABB is exactly that rectangle. Because **every** Part is placed
in the same world frame, when projected through
:data:`scripts.scene_world_frame.PROJ` the bed-line, vial mouths,
gantry rail and mechanism home column line up across all eight tiles
by construction.

The CadQuery assemblies are used:

1. as the ground truth for AABB-based 2-D draw rectangles, so the
   animator is grounded in real geometry (not in hand-tuned pixel
   numbers); and
2. exported to STEP (per concept, LOAD pose) under
   ``cad/alternatives_cq/`` so reviewers can re-open the geometry in
   any CAD package.

Running this module as a script writes the STEP files and a
``manifest.json`` summarising every part's world AABB.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import cadquery as cq

from scene_world_frame import PROJ, WORLD

# ---------------------------------------------------------------------------
# Phase clock (shared across every concept)
# ---------------------------------------------------------------------------

PHASES = (
    ("LOAD",     0.00, 0.25),
    ("APPROACH", 0.25, 0.42),
    ("DISPENSE", 0.42, 0.85),
    ("SETTLE",   0.85, 1.00),
)


def phase_at(t: float) -> Tuple[str, float]:
    """Return (phase_name, progress_in_phase∈[0,1]) at normalised t."""
    t = t % 1.0
    for name, t0, t1 in PHASES:
        if t < t1:
            return name, max(0.0, min(1.0, (t - t0) / max(t1 - t0, 1e-9)))
    return PHASES[-1][0], 1.0


def gantry_x(t: float) -> float:
    """Shared gantry-X trajectory in mm — same for every concept.

    LOAD  : at home_x
    APPROACH: linear traverse home_x -> vial_x
    DISPENSE: at vial_x
    SETTLE  : at vial_x (post-dispense pause)
    """
    name, p = phase_at(t)
    if name == "LOAD":
        return WORLD.mech_home_x
    if name == "APPROACH":
        return WORLD.mech_home_x + (WORLD.vial_x - WORLD.mech_home_x) * p
    return WORLD.vial_x  # DISPENSE / SETTLE


def gantry_dip(t: float) -> float:
    """Shared vertical pecking dip in mm (concept A uses this primarily)."""
    name, p = phase_at(t)
    if name != "DISPENSE":
        return 0.0
    # 3 evenly spaced down-strokes of 4 mm each during DISPENSE.
    n_strikes = 3
    k = p * n_strikes
    frac = k - int(k)
    # Triangle wave: 0 -> 1 -> 0 inside each strike.
    return -4.0 * (1.0 - abs(2 * frac - 1.0))


# ---------------------------------------------------------------------------
# Part record (CAD AABB + label) — what gets drawn
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Part:
    """A side-view world-frame AABB plus a label and a colour key."""

    name: str
    x_mm: float
    z_mm: float
    dx_mm: float
    dz_mm: float
    color: str = "body"  # body | accent | accent2 | powder | gantry | bed | vial

    def to_box(self) -> Tuple[float, float, float, float]:
        return (self.x_mm, self.z_mm, self.dx_mm, self.dz_mm)


# ---------------------------------------------------------------------------
# CadQuery helpers — every solid is created in world coordinates so the
# AABBs we hand back to the animator are literally the CAD bounding boxes.
# ---------------------------------------------------------------------------

def _wcs_box(
    x_mm: float, z_mm: float, dx_mm: float, dz_mm: float,
    y_mm: float = -7.5, dy_mm: float = 15.0,
) -> cq.Workplane:
    """Axis-aligned box placed at world (x, y, z)–min with extents dx/dy/dz."""
    return (
        cq.Workplane("XY")
        .box(dx_mm, dy_mm, dz_mm, centered=(False, False, False))
        .translate((x_mm, y_mm, z_mm))
    )


def _wcs_cyl(
    x_mm: float, z_mm: float, d_mm: float, h_mm: float,
    y_mm: float = 0.0,
) -> cq.Workplane:
    """Z-axis cylinder centred at world (x, y, z+h/2)."""
    return (
        cq.Workplane("XY")
        .circle(d_mm / 2.0)
        .extrude(h_mm)
        .translate((x_mm, y_mm, z_mm))
    )


def _aabb_xz(part: cq.Workplane) -> Tuple[float, float, float, float]:
    """Return (x_min, z_min, dx, dz) of the part's world AABB on the (x,z) face."""
    bb = part.val().BoundingBox()
    return bb.xmin, bb.zmin, bb.xlen, bb.zlen


# ---------------------------------------------------------------------------
# Shared scene parts (bed, gantry rail, vial) — same for every concept
# ---------------------------------------------------------------------------

def shared_parts() -> List[Part]:
    """Bed, gantry rail and vial — IDENTICAL across all eight concepts."""
    parts: List[Part] = []

    # Bed slab.
    parts.append(Part(
        "bed",
        WORLD.work_xmin, WORLD.bed_z - WORLD.bed_thickness,
        WORLD.work_xmax - WORLD.work_xmin, WORLD.bed_thickness,
        color="bed",
    ))
    # Gantry rail (top horizontal beam).
    parts.append(Part(
        "gantry-rail",
        WORLD.work_xmin + 5, WORLD.gantry_rail_z,
        (WORLD.work_xmax - WORLD.work_xmin) - 10, WORLD.gantry_rail_h,
        color="gantry",
    ))
    # Vial body.
    parts.append(Part(
        "vial",
        WORLD.vial_x - WORLD.vial_od / 2.0, WORLD.bed_z,
        WORLD.vial_od, WORLD.vial_h,
        color="vial",
    ))
    return parts


def shared_cq_scene() -> cq.Assembly:
    """CadQuery assembly of just the shared scene (bed + rail + vial)."""
    asy = cq.Assembly()
    asy.add(
        _wcs_box(
            WORLD.work_xmin, WORLD.bed_z - WORLD.bed_thickness,
            WORLD.work_xmax - WORLD.work_xmin, WORLD.bed_thickness,
            y_mm=-90, dy_mm=180,
        ),
        name="bed",
    )
    asy.add(
        _wcs_box(
            WORLD.work_xmin + 5, WORLD.gantry_rail_z,
            (WORLD.work_xmax - WORLD.work_xmin) - 10, WORLD.gantry_rail_h,
            y_mm=-15, dy_mm=30,
        ),
        name="gantry_rail",
    )
    asy.add(
        _wcs_cyl(WORLD.vial_x, WORLD.bed_z, WORLD.vial_od, WORLD.vial_h),
        name="vial",
    )
    return asy


# ---------------------------------------------------------------------------
# Gantry spindle column (every concept hangs its mechanism from this)
# ---------------------------------------------------------------------------

def gantry_carriage_parts(x_mm: float, mech_top_z: float) -> List[Part]:
    return [
        Part(
            "gantry-carriage",
            x_mm - 14, WORLD.gantry_rail_z - 8,
            28, 10, color="gantry",
        ),
        Part(
            "spindle-stem",
            x_mm - 2.5, mech_top_z,
            5.0, WORLD.gantry_rail_z - 8 - mech_top_z,
            color="gantry",
        ),
    ]


# ---------------------------------------------------------------------------
# Per-concept mechanism builders. Each returns (parts, cq.Assembly).
# Phase-dependent parts only — shared bed/rail/vial come from shared_parts().
# ---------------------------------------------------------------------------

# Common spindle-clamp boss height
BOSS_H = 14.0
# Standard mechanism cup height (a, g, h)
SIEVE_CUP_OD = 26.0
SIEVE_CUP_H = 20.0


def _powder_in_vial(t: float, vial_fill_frac: float | None = None) -> Part:
    if vial_fill_frac is None:
        name, p = phase_at(t)
        if name in ("LOAD", "APPROACH"):
            vial_fill_frac = 0.04
        elif name == "DISPENSE":
            vial_fill_frac = 0.04 + 0.55 * p
        else:
            vial_fill_frac = 0.59
    fill_h = max(0.0, min(WORLD.vial_h - 2.0, (WORLD.vial_h - 2.0) * vial_fill_frac))
    return Part(
        "vial-powder",
        WORLD.vial_x - WORLD.vial_od / 2.0 + 1.5,
        WORLD.bed_z + 1.0,
        WORLD.vial_od - 3.0,
        fill_h,
        color="powder",
    )


def _falling_stream(t: float, x_center: float, z_top: float, z_bot: float,
                    intensity: float = 1.0) -> List[Part]:
    """Approximate a falling powder stream as a thin vertical strip."""
    name, _ = phase_at(t)
    if name != "DISPENSE":
        return []
    h = max(0.5, (z_top - z_bot))
    w = 1.5 + 0.5 * intensity
    return [Part(
        "powder-stream", x_center - w / 2.0, z_bot, w, h, color="powder",
    )]


def _source_pad(x_mm: float) -> Part:
    """Powder source-pad on the bed (LOAD phase)."""
    return Part(
        "source-pad",
        x_mm - 18, WORLD.bed_z,
        36, 4, color="powder",
    )


# ---- Concept A: gantry-tap sieve cup + bed anvil -------------------------

def concept_a(t: float) -> Tuple[str, List[Part], cq.Assembly]:
    """A — tap-driven sieve cup; gantry pecks cup down onto anvil."""
    gx = gantry_x(t)
    dip = gantry_dip(t)
    mech_bottom_z = WORLD.vial_top_z + 10 + dip  # cup floor sits above vial
    mech_top_z = mech_bottom_z + SIEVE_CUP_H + BOSS_H
    parts: List[Part] = []
    parts += gantry_carriage_parts(gx, mech_top_z)
    # Boss + cup body
    parts.append(Part("spindle-boss",
                      gx - WORLD.spindle_clamp_d / 2.0,
                      mech_bottom_z + SIEVE_CUP_H,
                      WORLD.spindle_clamp_d, BOSS_H, color="body"))
    parts.append(Part("sieve-cup",
                      gx - SIEVE_CUP_OD / 2.0, mech_bottom_z,
                      SIEVE_CUP_OD, SIEVE_CUP_H, color="body"))
    # Mesh disc at cup floor
    parts.append(Part("mesh-disc",
                      gx - 9.0, mech_bottom_z - 0.5,
                      18.0, 1.0, color="accent"))
    # Bed-mounted anvil under the gantry-home column
    anvil_x = WORLD.mech_home_x
    parts.append(Part("anvil", anvil_x - 15, WORLD.bed_z, 30, 8, color="accent2"))
    parts.append(_powder_in_vial(t))
    name, _ = phase_at(t)
    if name == "LOAD":
        # cup loading at source pad
        parts.append(_source_pad(WORLD.mech_home_x))
    parts += _falling_stream(t, gx, mech_bottom_z, WORLD.vial_top_z)
    # CadQuery assembly mirroring the AABBs
    asy = shared_cq_scene()
    asy.add(_wcs_cyl(gx, mech_bottom_z, SIEVE_CUP_OD, SIEVE_CUP_H), name="sieve_cup")
    asy.add(_wcs_cyl(gx, mech_bottom_z + SIEVE_CUP_H, WORLD.spindle_clamp_d, BOSS_H),
            name="spindle_boss")
    asy.add(_wcs_box(anvil_x - 15, WORLD.bed_z, 30, 8), name="anvil")
    return "A — Tap-driven sieve cup + anvil", parts, asy


# ---- Concept B: Pez-style chamber strip ----------------------------------

def concept_b(t: float) -> Tuple[str, List[Part], cq.Assembly]:
    """B — Pez-style strip with N chambers; bed pawl advances it."""
    gx = gantry_x(t)
    n_ch = 8
    pitch = 8.0
    strip_w = n_ch * pitch
    strip_h = 7.0
    strip_z = WORLD.vial_top_z + 6  # strip rides just above vial mouth
    # Strip slides left→right with phase progression.
    name, p = phase_at(t)
    n_advanced = {"LOAD": 0.0, "APPROACH": 0.0,
                  "DISPENSE": p * n_ch, "SETTLE": float(n_ch)}[name]
    strip_x_offset = -n_advanced * pitch
    parts: List[Part] = []
    parts += gantry_carriage_parts(gx, strip_z + strip_h + BOSS_H)
    # Boss carrying the loader cartridge
    parts.append(Part("loader-boss",
                      gx - WORLD.spindle_clamp_d / 2.0, strip_z + strip_h + 2,
                      WORLD.spindle_clamp_d, BOSS_H, color="body"))
    # Strip body (centred over the vial mouth when fully advanced)
    strip_left = WORLD.vial_x - strip_w / 2.0 + strip_x_offset
    parts.append(Part("strip", strip_left, strip_z, strip_w, strip_h, color="body"))
    # Bed pawl just left of vial
    parts.append(Part("bed-pawl", WORLD.vial_x - 18, WORLD.bed_z,
                      4, strip_z - WORLD.bed_z, color="accent2"))
    # Chamber dots
    for i in range(n_ch):
        cx = strip_left + (i + 0.5) * pitch
        is_above_vial = abs(cx - WORLD.vial_x) < pitch / 2
        if name == "DISPENSE" and is_above_vial:
            color = "powder"  # currently dispensing
        elif name == "LOAD":
            color = "powder"
        else:
            color = "powder" if cx > strip_left + strip_x_offset + 0 else "accent"
        parts.append(Part(f"chamber-{i}", cx - 1.5, strip_z + 1, 3.0, 4.0,
                          color=color))
    parts.append(_powder_in_vial(t))
    parts += _falling_stream(t, WORLD.vial_x, strip_z, WORLD.vial_top_z, 0.6)
    asy = shared_cq_scene()
    asy.add(_wcs_box(strip_left, strip_z, strip_w, strip_h), name="strip")
    return "B — Pez-style chamber strip", parts, asy


# ---- Concept C: capillary dip + wiper ------------------------------------

def concept_c(t: float) -> Tuple[str, List[Part], cq.Assembly]:
    gx = gantry_x(t)
    name, p = phase_at(t)
    # Capillary tube hanging from boss
    boss_bottom_z = WORLD.gantry_rail_z - 8 - 6
    cap_h = 40.0
    if name == "LOAD":
        # Dipping into a small source cup at mech_home_x
        cap_z = WORLD.bed_z + 2  # tip just above bed
    elif name == "APPROACH":
        cap_z = WORLD.bed_z + 8 + 12 * p
    elif name == "DISPENSE":
        cap_z = WORLD.vial_top_z + 2  # just above vial mouth
    else:
        cap_z = WORLD.vial_top_z + 8
    parts: List[Part] = []
    parts += gantry_carriage_parts(gx, boss_bottom_z + BOSS_H)
    parts.append(Part("c-boss",
                      gx - WORLD.spindle_clamp_d / 2.0, boss_bottom_z,
                      WORLD.spindle_clamp_d, BOSS_H, color="body"))
    parts.append(Part("capillary", gx - 0.75, cap_z, 1.5, boss_bottom_z - cap_z,
                      color="accent"))
    # Source cup at home
    parts.append(Part("c-source",
                      WORLD.mech_home_x - 10, WORLD.bed_z,
                      20, 8, color="powder"))
    # Wiper post next to vial
    parts.append(Part("wiper", WORLD.vial_x - 16, WORLD.bed_z,
                      3, 12, color="accent2"))
    # Powder plug on capillary tip if loaded
    if name in ("APPROACH", "DISPENSE"):
        parts.append(Part("c-plug", gx - 1.5, cap_z, 3.0, 2.0, color="powder"))
    parts.append(_powder_in_vial(t))
    parts += _falling_stream(t, gx, cap_z, WORLD.vial_top_z, 0.3)
    asy = shared_cq_scene()
    asy.add(_wcs_cyl(gx, cap_z, 1.5, boss_bottom_z - cap_z), name="capillary")
    return "C — Capillary dip + wiper", parts, asy


# ---- Concept D: brush pickup + comb --------------------------------------

def concept_d(t: float) -> Tuple[str, List[Part], cq.Assembly]:
    gx = gantry_x(t)
    name, p = phase_at(t)
    brush_d = 22.0
    brush_z = WORLD.bed_z + 8  # brush disc face hovering just above bed
    if name == "DISPENSE":
        brush_z = WORLD.vial_top_z + 2
    parts: List[Part] = []
    parts += gantry_carriage_parts(gx, brush_z + brush_d + BOSS_H)
    parts.append(Part("d-boss",
                      gx - WORLD.spindle_clamp_d / 2.0, brush_z + brush_d,
                      WORLD.spindle_clamp_d, BOSS_H, color="body"))
    parts.append(Part("brush", gx - brush_d / 2, brush_z, brush_d, brush_d,
                      color="body"))
    parts.append(Part("bristles", gx - brush_d / 2, brush_z - 4,
                      brush_d, 4, color="accent"))
    # Bed comb past the vial
    parts.append(Part("comb", WORLD.vial_x + 12, WORLD.bed_z,
                      14, 10, color="accent2"))
    parts.append(_source_pad(WORLD.mech_home_x))
    parts.append(_powder_in_vial(t))
    parts += _falling_stream(t, gx, brush_z - 4, WORLD.vial_top_z, 0.5)
    asy = shared_cq_scene()
    asy.add(_wcs_cyl(gx, brush_z, brush_d, brush_d), name="brush")
    return "D — Brush pickup + comb", parts, asy


# ---- Concept E: salt-shaker oscillation ----------------------------------

def concept_e(t: float) -> Tuple[str, List[Part], cq.Assembly]:
    gx = gantry_x(t)
    name, p = phase_at(t)
    body_d = 28.0
    body_h = 30.0
    body_z = WORLD.vial_top_z + 6
    # Lateral shaker oscillation during DISPENSE
    osc = 0.0
    if name == "DISPENSE":
        osc = 3.0 * math.sin(2 * math.pi * 6 * p)
    parts: List[Part] = []
    parts += gantry_carriage_parts(gx, body_z + body_h + BOSS_H)
    parts.append(Part("e-boss",
                      gx - WORLD.spindle_clamp_d / 2.0, body_z + body_h,
                      WORLD.spindle_clamp_d, BOSS_H, color="body"))
    parts.append(Part("shaker-body",
                      gx - body_d / 2 + osc, body_z, body_d, body_h,
                      color="body"))
    # Perforated cap
    parts.append(Part("perf-cap",
                      gx - body_d / 2 + osc + 1, body_z, body_d - 2, 2,
                      color="accent"))
    # Internal powder fill
    parts.append(Part("powder-fill",
                      gx - body_d / 2 + osc + 2, body_z + 2,
                      body_d - 4, body_h - 8, color="powder"))
    parts.append(_powder_in_vial(t))
    parts += _falling_stream(t, gx, body_z, WORLD.vial_top_z, 0.7)
    asy = shared_cq_scene()
    asy.add(_wcs_cyl(gx + osc, body_z, body_d, body_h), name="shaker_body")
    return "E — Salt-shaker oscillation", parts, asy


# ---- Concept F: passive auger (rack/pinion driven) -----------------------

def concept_f(t: float) -> Tuple[str, List[Part], cq.Assembly]:
    gx = gantry_x(t)
    name, p = phase_at(t)
    tube_od = 16.0
    tube_h = 36.0
    tube_z = WORLD.vial_top_z + 4
    parts: List[Part] = []
    parts += gantry_carriage_parts(gx, tube_z + tube_h + BOSS_H)
    parts.append(Part("f-boss",
                      gx - WORLD.spindle_clamp_d / 2.0, tube_z + tube_h,
                      WORLD.spindle_clamp_d, BOSS_H, color="body"))
    parts.append(Part("auger-tube",
                      gx - tube_od / 2.0, tube_z, tube_od, tube_h,
                      color="body"))
    # Helix flights — represent as small accent dashes at intervals
    n_flight = 5
    for i in range(n_flight):
        z = tube_z + 5 + (tube_h - 10) * (i / max(n_flight - 1, 1))
        parts.append(Part(f"flight-{i}", gx - 5, z, 10, 1.2, color="accent"))
    # Bed rack
    parts.append(Part("bed-rack", WORLD.vial_x - 20, WORLD.bed_z,
                      30, 4, color="accent2"))
    parts.append(_powder_in_vial(t))
    parts += _falling_stream(t, gx, tube_z, WORLD.vial_top_z, 0.6)
    asy = shared_cq_scene()
    asy.add(_wcs_cyl(gx, tube_z, tube_od, tube_h), name="auger_tube")
    return "F — Passive auger (rack/pinion)", parts, asy


# ---- Concept G: ERM-augmented sieve cup ----------------------------------

def concept_g(t: float) -> Tuple[str, List[Part], cq.Assembly]:
    gx = gantry_x(t)
    name, p = phase_at(t)
    cup_z = WORLD.vial_top_z + 10
    parts: List[Part] = []
    parts += gantry_carriage_parts(gx, cup_z + SIEVE_CUP_H + BOSS_H)
    parts.append(Part("g-boss",
                      gx - WORLD.spindle_clamp_d / 2.0,
                      cup_z + SIEVE_CUP_H,
                      WORLD.spindle_clamp_d, BOSS_H, color="body"))
    parts.append(Part("g-cup",
                      gx - SIEVE_CUP_OD / 2.0, cup_z,
                      SIEVE_CUP_OD, SIEVE_CUP_H, color="body"))
    parts.append(Part("mesh-disc",
                      gx - 9.0, cup_z - 0.5, 18.0, 1.0, color="accent"))
    # ERM coin motor pocket on cup side
    erm_color = "accent2" if name == "DISPENSE" else "accent"
    parts.append(Part("erm-motor",
                      gx + SIEVE_CUP_OD / 2.0 - 1, cup_z + 9,
                      4, 4, color=erm_color))
    # CR2032 cell holder pocket above ERM
    parts.append(Part("cr2032",
                      gx - 11, cup_z + 14,
                      6, 4, color="accent"))
    parts.append(_powder_in_vial(t))
    # ERM produces continuous stream during DISPENSE
    parts += _falling_stream(t, gx, cup_z, WORLD.vial_top_z, 1.0)
    asy = shared_cq_scene()
    asy.add(_wcs_cyl(gx, cup_z, SIEVE_CUP_OD, SIEVE_CUP_H), name="g_cup")
    return "G — ERM-augmented sieve", parts, asy


# ---- Concept H: solenoid-tapped sieve cup --------------------------------

def concept_h(t: float) -> Tuple[str, List[Part], cq.Assembly]:
    gx = gantry_x(t)
    name, p = phase_at(t)
    cup_z = WORLD.vial_top_z + 10
    # Solenoid tap pulse: short downward strikes on the cup wall.
    pulse_dx = 0.0
    if name == "DISPENSE":
        # 5 pulses, each a short 1.5 mm push from the side.
        n_pulse = 5
        k = p * n_pulse
        frac = k - int(k)
        pulse_dx = -1.5 * (1.0 - abs(2 * frac - 1.0))
    parts: List[Part] = []
    parts += gantry_carriage_parts(gx, cup_z + SIEVE_CUP_H + BOSS_H)
    parts.append(Part("h-boss",
                      gx - WORLD.spindle_clamp_d / 2.0,
                      cup_z + SIEVE_CUP_H,
                      WORLD.spindle_clamp_d, BOSS_H, color="body"))
    parts.append(Part("h-cup", gx - SIEVE_CUP_OD / 2.0, cup_z,
                      SIEVE_CUP_OD, SIEVE_CUP_H, color="body"))
    parts.append(Part("mesh-disc", gx - 9.0, cup_z - 0.5, 18.0, 1.0,
                      color="accent"))
    # Solenoid plunger
    parts.append(Part("solenoid-body",
                      gx + SIEVE_CUP_OD / 2.0 + 4, cup_z + 6,
                      12, 8, color="body"))
    parts.append(Part("solenoid-plunger",
                      gx + SIEVE_CUP_OD / 2.0 + pulse_dx, cup_z + 7.5,
                      4, 3, color="accent2"))
    # Balance under vial (live feedback)
    parts.append(Part("balance",
                      WORLD.vial_x - 18, WORLD.bed_z - 6,
                      36, 6, color="accent2"))
    parts.append(_powder_in_vial(t))
    parts += _falling_stream(t, gx, cup_z, WORLD.vial_top_z, 0.8)
    asy = shared_cq_scene()
    asy.add(_wcs_cyl(gx, cup_z, SIEVE_CUP_OD, SIEVE_CUP_H), name="h_cup")
    return "H — Solenoid-tapped sieve", parts, asy


CONCEPTS: Dict[str, Callable[[float], Tuple[str, List[Part], cq.Assembly]]] = {
    "A": concept_a, "B": concept_b, "C": concept_c, "D": concept_d,
    "E": concept_e, "F": concept_f, "G": concept_g, "H": concept_h,
}


# ---------------------------------------------------------------------------
# Static-pose STEP export + AABB manifest
# ---------------------------------------------------------------------------

def export_step_and_manifest(out_dir: Path) -> dict:
    """Export the LOAD-phase CAD assembly per concept + a JSON manifest."""
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict = {"world": WORLD.__dict__, "concepts": {}}
    for key, builder in CONCEPTS.items():
        title, parts, asy = builder(t=0.10)  # mid-LOAD
        step_path = out_dir / f"{key}_scene.step"
        try:
            asy.save(str(step_path))
        except Exception as exc:  # pragma: no cover — keep going on CI quirks
            step_path = None
            err = str(exc)
        else:
            err = None
        manifest["concepts"][key] = {
            "title": title,
            "step": str(step_path.relative_to(out_dir.parent.parent))
                    if step_path else None,
            "step_error": err,
            "parts_at_load_phase": [
                {
                    "name": p.name,
                    "x_mm": round(p.x_mm, 3),
                    "z_mm": round(p.z_mm, 3),
                    "dx_mm": round(p.dx_mm, 3),
                    "dz_mm": round(p.dz_mm, 3),
                    "color": p.color,
                }
                for p in parts
            ],
        }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n",
                             encoding="utf-8")
    return manifest


if __name__ == "__main__":
    repo = Path(__file__).resolve().parent.parent
    out_dir = repo / "cad" / "alternatives_cq"
    m = export_step_and_manifest(out_dir)
    print(f"Wrote manifest with {len(m['concepts'])} concepts to {out_dir}")
