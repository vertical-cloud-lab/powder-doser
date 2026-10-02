"""Geometry helpers shared by the Powder Doser parts.

Contains an involute spur-gear generator and a helical-screw (auger fin)
generator built only from ``cadquery`` primitives so every output is a clean,
manifold B-rep solid suitable for STEP export and FDM printing.
"""
from __future__ import annotations

import math
import numpy as np
import cadquery as cq


# --------------------------------------------------------------------------
# Involute spur gear
# --------------------------------------------------------------------------
def _inv_at(r: float, rb: float) -> float:
    """Involute roll function at radius ``r`` for base radius ``rb``."""
    r = max(r, rb)
    a = math.acos(max(-1.0, min(1.0, rb / r)))
    return math.tan(a) - a


def _tooth_face_pts(module, teeth, pressure_angle, rot, backlash, pts_per_flank):
    a = math.radians(pressure_angle)
    r = module * teeth / 2.0
    rb = r * math.cos(a)
    ra = r + module
    rf = max(r - 1.25 * module, 0.1)
    r_start = max(rb, rf)
    s_pitch = math.pi * module / 2.0 - backlash
    half_ang_pitch = s_pitch / (2.0 * r)
    beta = half_ang_pitch + _inv_at(r, rb)
    base_ang = beta - _inv_at(r_start, rb)
    radii = np.linspace(r_start, ra, pts_per_flank)

    pts = []
    # root foot on the right flank, then up the right flank
    if r_start > rf + 1e-6:
        pts.append((rf * math.cos(rot + base_ang), rf * math.sin(rot + base_ang)))
    for rr in radii:
        th = rot + beta - _inv_at(rr, rb)
        pts.append((rr * math.cos(th), rr * math.sin(th)))
    # tip arc
    tip_r = beta - _inv_at(ra, rb)
    for t in np.linspace(tip_r, -tip_r, 5)[1:-1]:
        pts.append((ra * math.cos(rot + t), ra * math.sin(rot + t)))
    # down the left flank
    for rr in reversed(radii):
        th = rot - (beta - _inv_at(rr, rb))
        pts.append((rr * math.cos(th), rr * math.sin(th)))
    if r_start > rf + 1e-6:
        pts.append((rf * math.cos(rot - base_ang), rf * math.sin(rot - base_ang)))
    return pts, rf


def gear_solid(module: float, teeth: int, pressure_angle: float,
               face_width: float, backlash: float = 0.0,
               bore_d: float = 0.0, pts_per_flank: int = 14):
    """Spur gear solid (teeth in XY, extruded +Z).

    Built robustly as a root-circle disc fused with one prism per tooth so the
    profile can never self-intersect at the closing seam.
    """
    rf = max(module * teeth / 2.0 - 1.25 * module, 0.1)
    # solid root disc up to just past the dedendum circle
    gear = cq.Workplane("XY").circle(rf + 0.05).extrude(face_width)
    tooth_ang = 2.0 * math.pi / teeth
    for i in range(teeth):
        pts, _ = _tooth_face_pts(module, teeth, pressure_angle,
                                 i * tooth_ang, backlash, pts_per_flank)
        clean = [pts[0]]
        for p in pts[1:]:
            if (p[0] - clean[-1][0]) ** 2 + (p[1] - clean[-1][1]) ** 2 > 1e-9:
                clean.append(p)
        tooth = cq.Workplane("XY").polyline(clean).close().extrude(face_width)
        gear = gear.union(tooth)
    if bore_d > 0:
        gear = gear.faces("<Z").workplane().hole(bore_d)
    return gear


def gear_outline(module: float, teeth: int, pressure_angle: float,
                 backlash: float = 0.0, pts_per_flank: int = 14):
    """Closed outline points for a full involute gear (debug / plotting)."""
    tooth_ang = 2.0 * math.pi / teeth
    rf = max(module * teeth / 2.0 - 1.25 * module, 0.1)
    pts = []
    for i in range(teeth):
        tp, _ = _tooth_face_pts(module, teeth, pressure_angle,
                                i * tooth_ang, backlash, pts_per_flank)
        pts.extend(tp)
    return pts


def gear_dims(module: float, teeth: int):
    """Convenience: (pitch_d, tip_d, root_d)."""
    r = module * teeth / 2.0
    return (2 * r, 2 * (r + module), 2 * max(r - 1.25 * module, 0.1))


# --------------------------------------------------------------------------
# Helical auger screw (shaft + single-start fin) via twist-extrude
# --------------------------------------------------------------------------
def screw_solid(height: float, pitch: float, shaft_r: float,
                fin_outer_r: float, fin_thick: float,
                fin_inner_r: float = 0.0):
    """Single-start Archimedean screw: a central shaft plus one helical fin.

    Built like the SCAD ``linear_extrude(twist=...)`` of a 2-D tooth: a radial
    fin bar unioned with the shaft circle, twisted one turn per ``pitch``.
    """
    twist = -360.0 * height / pitch          # right-handed helix
    # shaft + radial fin bar, each twist-extruded one turn per ``pitch``
    shaft = cq.Workplane("XY").circle(shaft_r).twistExtrude(height, twist)
    fin = (
        cq.Workplane("XY")
        .center(fin_inner_r + (fin_outer_r - fin_inner_r) / 2.0, 0)
        .rect(fin_outer_r - fin_inner_r, fin_thick)
        .twistExtrude(height, twist)
    )
    return shaft.union(fin)
