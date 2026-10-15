"""Involute spur gears.

The defaults reproduce the Fusion 360 "SpurGear" add-in that generated every
gear in this project (stepper pinion, servo pinion, auger gear and the
mounting plate's two 28T gears), as measured off their STEP exports:

* addendum 1.0 m (outside diameter (N + 2) m), dedendum 1.157 m;
* tooth thickness pi m / 2 on the pitch circle (zero backlash);
* the flank is a true involute from the base circle to the outside circle,
  continued radially down to the root circle where the base circle lies above
  it (fewer than about 42 teeth at 20 degrees);
* 0.5 mm fillets where the flanks meet the root circle;
* tooth 0 centred on +X (``tooth_angle`` rotates the pattern).

Every gear is centred on the Z axis and runs from z = 0 to z = width.
Public API (keep stable; other models import it)::

    spur_gear(module, teeth, width, pressure_angle=20.0, *, backlash=0.0,
              addendum=1.0, dedendum=1.157, root_fillet=0.5, bore=0.0,
              tooth_angle=0.0) -> bd.Part
    gear_profile(module, teeth, pressure_angle=20.0, *, ...) -> bd.Face
    pitch_diameter / base_diameter / outside_diameter / root_diameter /
    centre_distance
"""
from __future__ import annotations

import math

from cadgen import build123d as bd

ADDENDUM = 1.0        # x module (Fusion SpurGear add-in)
DEDENDUM = 1.157      # x module (Fusion SpurGear add-in, small modules)
ROOT_FILLET = 0.5     # mm, as on every reference gear
FLANK_SAMPLES = 16    # interpolation points per involute flank


def pitch_diameter(module: float, teeth: int) -> float:
    return module * teeth


def base_diameter(module: float, teeth: int, pressure_angle: float = 20.0) -> float:
    return module * teeth * math.cos(math.radians(pressure_angle))


def outside_diameter(module: float, teeth: int, addendum: float = ADDENDUM) -> float:
    return module * (teeth + 2.0 * addendum)


def root_diameter(module: float, teeth: int, dedendum: float = DEDENDUM) -> float:
    return module * (teeth - 2.0 * dedendum)


def centre_distance(module: float, teeth_a: int, teeth_b: int) -> float:
    """Standard (unshifted) centre distance of two meshing spur gears."""
    return module * (teeth_a + teeth_b) / 2.0


def _inv(alpha: float) -> float:
    return math.tan(alpha) - alpha


def _rot(p: tuple[float, float], a: float, mirror: bool = False) -> tuple[float, float, float]:
    x, y = p[0], (-p[1] if mirror else p[1])
    c, s = math.cos(a), math.sin(a)
    return (x * c - y * s, x * s + y * c, 0.0)


def _flank(module, teeth, alpha, backlash, addendum, dedendum, root_fillet):
    """One flank of a tooth centred on +X: the falling (+Y) side, in 2D.

    Returns (rr, ra, fillet, line, involute) where ``fillet`` is the
    (root point, mid, flank point) of the root-fillet arc or None, ``line``
    the (start, end) of the radial run below the base circle or None, and
    ``involute`` the flank samples from its lowest point up to the outside
    circle. The fillet is solved against the actual flank (radial line and/or
    involute), so it may roll past the base circle like Fusion's 3D fillet."""
    rp = module * teeth / 2.0
    rb = rp * math.cos(alpha)
    ra = rp + addendum * module
    rr = rp - dedendum * module
    if not rr < rp < ra:
        raise ValueError("root < pitch < outside radius violated")
    psi_b = math.pi / (2 * teeth) - backlash / (4.0 * rp) + _inv(alpha)

    def psi(r: float) -> float:          # half tooth angle at radius r >= rb
        return psi_b - _inv(math.acos(min(1.0, rb / r)))

    def pt(r: float) -> tuple[float, float]:
        a = psi_b if r <= rb else psi(r)
        return (r * math.cos(a), r * math.sin(a))

    if psi(ra) <= 0.0:
        raise ValueError("pointed teeth: reduce addendum or pressure angle")
    r_low = max(rb, rr)                  # flank's lowest point without a fillet
    fillet = None
    if root_fillet > 0.0:
        rho, rc = root_fillet, rr + root_fillet   # fillet centre lies on radius rc

        def centre(r: float) -> tuple[float, float]:
            # flank point + rho * unit normal towards the gap (+angle side)
            h = 1e-6
            (x0, y0), (x1, y1) = pt(max(rr, r - h) if r > rb else r), pt(r + h)
            tx, ty = x1 - x0, y1 - y0
            n = math.hypot(tx, ty)
            x, y = pt(r)
            return (x - rho * ty / n, y + rho * tx / n)

        r_t = math.sqrt(rc * rc - rho * rho)     # tangent radius on a radial line
        if r_t > rb or rb <= rr:                 # tangent point is on the involute
            lo, hi = r_low, ra
            if math.hypot(*centre(lo)) > rc:
                raise ValueError("root fillet does not fit")
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                if math.hypot(*centre(mid)) < rc:
                    lo = mid
                else:
                    hi = mid
            r_t = 0.5 * (lo + hi)
        if r_t >= ra:
            raise ValueError("root fillet too large")
        cx, cy = centre(r_t)
        t = pt(r_t)
        k = rr / math.hypot(cx, cy)
        root = (cx * k, cy * k)
        bx, by = (t[0] - cx) + (root[0] - cx), (t[1] - cy) + (root[1] - cy)
        nb = math.hypot(bx, by)
        mid = (cx + rho * bx / nb, cy + rho * by / nb)
        if math.atan2(root[1], root[0]) >= math.pi / teeth:
            raise ValueError("root fillets overlap; reduce root_fillet")
        fillet = (root, mid, t)
        r_low = r_t
    line = None
    if rb > rr and r_low < rb - 1e-9:
        line = (pt(r_low), pt(rb))
    r0 = max(r_low, rb)
    t0 = math.sqrt(max(0.0, (r0 / rb) ** 2 - 1.0))
    ta = math.sqrt((ra / rb) ** 2 - 1.0)
    radii = [rb * math.sqrt(1.0 + (t0 + (ta - t0) * i / (FLANK_SAMPLES - 1)) ** 2)
             for i in range(FLANK_SAMPLES)]
    radii[0], radii[-1] = r0, ra
    return rr, ra, fillet, line, [pt(r) for r in radii]


def gear_profile(
    module: float,
    teeth: int,
    pressure_angle: float = 20.0,
    *,
    backlash: float = 0.0,
    addendum: float = ADDENDUM,
    dedendum: float = DEDENDUM,
    root_fillet: float = ROOT_FILLET,
    tooth_angle: float = 0.0,
) -> bd.Face:
    """Closed 2D outline (in the XY plane, centred on the origin) of a spur gear."""
    if teeth < 5:
        raise ValueError("need at least 5 teeth")
    rr, ra, fillet, line, inv = _flank(module, teeth, math.radians(pressure_angle),
                                       backlash, addendum, dedendum, root_fillet)
    root_pt = fillet[0] if fillet else (line[0] if line else inv[0])
    gamma = math.atan2(root_pt[1], root_pt[0])     # root-land end, from tooth centre
    pitch = 2.0 * math.pi / teeth
    phase = math.radians(tooth_angle)
    E = bd.Edge
    edges: list[bd.Edge] = []
    for k in range(teeth):
        c = phase + k * pitch
        # rising (-Y, mirrored) flank, root to tip
        if fillet:
            edges.append(E.make_three_point_arc(*(_rot(p, c, True) for p in fillet)))
        if line:
            edges.append(E.make_line(_rot(line[0], c, True), _rot(line[1], c, True)))
        edges.append(E.make_spline([_rot(p, c, True) for p in inv]))
        edges.append(E.make_three_point_arc(_rot(inv[-1], c, True), _rot((ra, 0.0), c),
                                            _rot(inv[-1], c)))
        # falling (+Y) flank, tip to root
        edges.append(E.make_spline([_rot(p, c) for p in reversed(inv)]))
        if line:
            edges.append(E.make_line(_rot(line[1], c), _rot(line[0], c)))
        if fillet:
            edges.append(E.make_three_point_arc(*(_rot(p, c) for p in reversed(fillet))))
        # root land to the next tooth
        a1, a2 = c + gamma, c + pitch - gamma
        edges.append(E.make_three_point_arc(_rot((rr, 0.0), a1), _rot((rr, 0.0), 0.5 * (a1 + a2)),
                                            _rot((rr, 0.0), a2)))
    face = bd.Face(bd.Wire(edges))
    if face.normal_at().Z < 0:
        face = -face
    return face


def spur_gear(
    module: float,
    teeth: int,
    width: float,
    pressure_angle: float = 20.0,
    *,
    backlash: float = 0.0,
    addendum: float = ADDENDUM,
    dedendum: float = DEDENDUM,
    root_fillet: float = ROOT_FILLET,
    bore: float = 0.0,
    tooth_angle: float = 0.0,
) -> bd.Part:
    """Straight spur gear on the Z axis, z = 0 .. width, tooth 0 centred on
    ``tooth_angle`` (degrees from +X). ``bore`` > 0 cuts a plain centre hole."""
    face = gear_profile(module, teeth, pressure_angle, backlash=backlash,
                        addendum=addendum, dedendum=dedendum,
                        root_fillet=root_fillet, tooth_angle=tooth_angle)
    gear = bd.extrude(face, amount=width, dir=(0, 0, 1))
    if bore > 0.0:
        gear = gear - bd.Cylinder(bore / 2.0, width,
                                  align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    return gear
