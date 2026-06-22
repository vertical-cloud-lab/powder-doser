"""Reusable geometry helpers: involute spur gears, helical augers and threads.

These are intentionally self-contained (only CadQuery / OCP) so the part
builders in :mod:`build` stay declarative.
"""

import math

import cadquery as cq
from cadquery import Vector


# --------------------------------------------------------------------------- #
# Involute spur gears
# --------------------------------------------------------------------------- #
def _involute_points(base_r, start_r, end_r, n=12):
    """Sample an involute curve from ``start_r`` (>=base_r) to ``end_r``."""
    pts = []
    r0 = max(start_r, base_r)
    for i in range(n + 1):
        r = r0 + (end_r - r0) * i / n
        # involute parameter
        a = math.sqrt(max(r * r - base_r * base_r, 0.0)) / base_r
        # involute of a circle, parameterised by roll angle a
        x = base_r * (math.cos(a) + a * math.sin(a))
        y = base_r * (math.sin(a) - a * math.cos(a))
        pts.append((x, y))
    return pts


def gear_tooth_profile(module, teeth, pressure_angle=20.0, backlash=0.15,
                       tip_d=None, root_d=None):
    """Return a list of (x, y) points for the full gear outline (one closed wire).

    Standard full-depth involute teeth.  ``tip_d`` / ``root_d`` override the
    computed addendum / dedendum circles so the printed gears match the
    spec-sheet tip and root diameters exactly.
    """
    m = module
    z = teeth
    pa = math.radians(pressure_angle)
    pitch_r = m * z / 2.0
    base_r = pitch_r * math.cos(pa)
    add_r = (tip_d / 2.0) if tip_d else (pitch_r + m)
    ded_r = (root_d / 2.0) if root_d else (pitch_r - 1.25 * m)
    ded_r = max(ded_r, 0.1)

    # tooth thickness (angular) at the pitch circle, minus backlash
    t_pitch = (math.pi * m / 2.0) - backlash
    half_ang_pitch = t_pitch / (2.0 * pitch_r)

    # involute angular position at the pitch circle (relative to tooth centre)
    def inv(a):
        return math.tan(a) - a

    inv_pa = inv(pa)
    # angle from tooth centreline to the involute start on the base circle
    base_offset = half_ang_pitch + inv_pa

    flank = _involute_points(base_r, max(ded_r, base_r), add_r, n=10)
    # rotate one flank so the pitch point lands at +base_offset from centre
    # find the involute angle at pitch radius to align
    a_pitch = math.sqrt(max(pitch_r ** 2 - base_r ** 2, 0.0)) / base_r
    theta_at_pitch = math.atan2(
        base_r * (math.sin(a_pitch) - a_pitch * math.cos(a_pitch)),
        base_r * (math.cos(a_pitch) + a_pitch * math.sin(a_pitch)),
    )
    rot = base_offset - theta_at_pitch

    def rotate(pt, ang):
        c, s = math.cos(ang), math.sin(ang)
        return (pt[0] * c - pt[1] * s, pt[0] * s + pt[1] * c)

    pts = []
    tooth_ang = 2 * math.pi / z
    for k in range(z):
        centre = k * tooth_ang
        # right flank (mirror of left), built from base->tip
        left = [rotate(p, rot) for p in flank]
        right = [rotate((p[0], -p[1]), -rot) for p in flank]
        # if dedendum below base circle, add a radial segment to the root
        if ded_r < base_r:
            r_start = (math.cos(rot) * base_r, math.sin(rot) * base_r)
            left = [(ded_r * math.cos(rot), ded_r * math.sin(rot))] + left
            right = [(ded_r * math.cos(-rot), ded_r * math.sin(-rot))] + right
        # order: up the left flank, across the tip, down the right flank
        seq = list(reversed(right)) + left
        for p in seq:
            pts.append(rotate(p, centre))
    return pts


def spur_gear(module, teeth, face, pressure_angle=20.0, backlash=0.15,
              tip_d=None, root_d=None, bore_d=None):
    """Build an extruded involute spur gear solid centred on Z, face along +Z."""
    pts = gear_tooth_profile(module, teeth, pressure_angle, backlash,
                             tip_d=tip_d, root_d=root_d)
    wp = cq.Workplane("XY").polyline(pts).close().extrude(face)
    if bore_d:
        wp = wp.faces(">Z").workplane().hole(bore_d)
    return wp


def gear_ring(module, teeth, face, bore_d, pressure_angle=20.0, backlash=0.15,
              tip_d=None, root_d=None):
    """An *annular* gear band: external teeth, an open bore straight through.

    Used for the auger drive band, where the Ø21 bore must never be sealed.
    """
    return spur_gear(module, teeth, face, pressure_angle, backlash,
                     tip_d=tip_d, root_d=root_d, bore_d=bore_d)


# --------------------------------------------------------------------------- #
# Helical fin (Archimedean screw)
# --------------------------------------------------------------------------- #
def helical_fin(r_inner, r_outer, thickness, pitch, height, z0=0.0):
    """Sweep a rectangular fin cross-section along a helix.

    The fin is a flat annular ribbon of radial extent ``r_inner..r_outer`` and
    axial ``thickness``, wound at ``pitch`` mm/turn over ``height`` mm starting
    at ``z0``.
    """
    turns = height / pitch
    helix = cq.Wire.makeHelix(pitch=pitch, height=height, radius=r_inner)
    helix = helix.translate(Vector(0, 0, z0))
    path = cq.Workplane(obj=helix)
    # profile: a rectangle in the radial(X)/axial(Z) plane at the helix start.
    # ``center`` in the XZ workplane maps (x -> global X, y -> global Z).
    width = r_outer - r_inner
    prof = (
        cq.Workplane("XZ")
        .center(r_inner + width / 2.0, z0)
        .rect(width, thickness)
    )
    swept = prof.sweep(path, isFrenet=True)
    return swept


def auger_screw(shaft_r, fin_r_inner, fin_r_outer, fin_thk, pitch,
                screw_top_z, screw_bottom_z=0.0):
    """Central shaft + continuous helical fin between the given Z levels."""
    height = screw_top_z - screw_bottom_z
    shaft = (
        cq.Workplane("XY")
        .circle(shaft_r)
        .extrude(screw_top_z)
    )
    fin = helical_fin(fin_r_inner, fin_r_outer, fin_thk, pitch, height,
                      z0=screw_bottom_z)
    return shaft.union(fin)


# --------------------------------------------------------------------------- #
# External / internal printed threads (single-start trapezoidal-ish)
# --------------------------------------------------------------------------- #
def thread_ridge(major_r, minor_r, pitch, length, half_angle=58.0,
                 internal=False, clearance=0.0, z0=0.0):
    """A single-start helical thread ridge swept along a helix.

    The 2D profile is a triangle (half-angle ``half_angle``) between the minor
    and major radius.  ``internal`` grows the profile radially inward by
    ``clearance`` for a nut/cap.
    """
    depth = major_r - minor_r
    if internal:
        # internal thread lives on a cap; grow it radially for a hand fit
        major_r = major_r + clearance
        minor_r = minor_r + clearance

    helix = cq.Wire.makeHelix(pitch=pitch, height=length, radius=minor_r)
    helix = helix.translate(Vector(0, 0, z0))
    path = cq.Workplane(obj=helix)
    half_w = pitch / 2.0  # axial half-width footprint of the tooth at the root
    # triangular profile in the radial(X)/axial(Z) plane, apex outward, at z0.
    prof = (
        cq.Workplane("XZ")
        .polyline([
            (minor_r, z0 - half_w),
            (minor_r, z0 + half_w),
            (major_r, z0),
        ])
        .close()
    )
    ridge = prof.sweep(path, isFrenet=True)
    return ridge
