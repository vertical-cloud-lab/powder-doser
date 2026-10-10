"""Parametric surface meshes of the rotating-tube auger for LIGGGHTS.

The rig's auger (``Auger4.stl``, Sam's "main design") is one rotating
part: a 21 mm bore tube with an internal helical flight fused to the
wall (10 mm pitch, about 2.2 mm thick, open 8 mm core), ending in a
32 deg half-angle cone that necks down to a 2.5 mm exit hole. Measured
from the STL by slicing (see README.md):

    bore radius R          10.5 mm
    flight inner radius     4.0 mm   (open core, no shaft)
    pitch                  10.0 mm   (right-handed)
    flight axial thickness  2.2 mm
    funnel                 cone r = 1.22 mm at z = 0 -> 8.85 mm at z = 12,
                           then a flat shelf out to the bore

Everything is generated with the auger axis on +z and the exit hole at
z = 0, so LIGGGHTS can spin the mesh with ``fix move/mesh rotate``
about the z axis and tilt *gravity* instead of the geometry. Positive
rotation (counter-clockwise about +z) drives a right-handed flight
towards the exit.

Only the bottom ``n_turns`` of the 250 mm tube are meshed; a feed zone
above the last flight is kept topped up by particle insertion, which
stands in for the rest of the powder column.

Meshes are written as ASCII STL in millimetres (LIGGGHTS scales them
with ``scale 0.001``).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

import numpy as np


@dataclass
class AugerParams:
    bore_r: float = 10.5          # mm, tube inner radius
    core_r: float = 4.0           # mm, flight inner edge (0 => flight reaches a shaft)
    shaft_r: float = 0.0          # mm, solid central shaft radius (0 => open core)
    pitch: float = 10.0           # mm per turn
    flight_t: float = 2.2         # mm, axial flight thickness
    n_turns: float = 4.0          # simulated flight turns above the funnel
    starts: int = 1               # number of flight starts
    funnel_h: float = 12.0        # mm, cone height
    exit_r: float = 1.25          # mm, exit hole radius
    funnel_top_r: float = 8.85    # mm, cone radius at its top (shelf out to bore_r)
    feed_h: float = 14.0          # mm of open bore above the last flight (feed zone)
    n_theta: int = 48             # circumferential resolution (sagitta 0.02 mm at R = 10.5)
    dz: float = 2.0               # mm, target axial edge length
    dr: float = 1.7               # mm, target radial edge length on the flight

    @property
    def flight_top(self) -> float:
        return self.funnel_h + self.n_turns * self.pitch

    @property
    def z_top(self) -> float:
        return self.flight_top + self.flight_t + self.feed_h


def _quad(tris, a, b, c, d):
    """Two triangles for quad a-b-c-d (counter-clockwise)."""
    tris.append((a, b, c))
    tris.append((a, c, d))


def _surface_of_revolution(r_of_s, z_of_s, s, n_theta, theta0=0.0, theta1=2 * np.pi):
    """Triangles of a surface of revolution sampled at parameters s."""
    th = np.linspace(theta0, theta1, n_theta + 1)
    tris = []
    for i in range(len(s) - 1):
        r0, r1 = r_of_s(s[i]), r_of_s(s[i + 1])
        z0, z1 = z_of_s(s[i]), z_of_s(s[i + 1])
        for j in range(n_theta):
            p = [
                (r0 * np.cos(th[j]), r0 * np.sin(th[j]), z0),
                (r0 * np.cos(th[j + 1]), r0 * np.sin(th[j + 1]), z0),
                (r1 * np.cos(th[j + 1]), r1 * np.sin(th[j + 1]), z1),
                (r1 * np.cos(th[j]), r1 * np.sin(th[j]), z1),
            ]
            _quad(tris, *p)
    return tris


def _helical_flight(p: AugerParams, phase: float):
    """Thick helical ribbon between core_r and bore_r, one start."""
    tris = []
    r_in = max(p.core_r, p.shaft_r)
    n_r = max(2, int(np.ceil((p.bore_r - r_in) / p.dr)))
    rs = np.linspace(r_in, p.bore_r, n_r + 1)
    lead = p.pitch * p.starts  # axial advance per revolution of one start
    turns = p.n_turns / p.starts  # revolutions each start makes over n_turns pitches
    n_phi = int(np.ceil(turns * p.n_theta))
    phis = np.linspace(0.0, 2 * np.pi * turns, n_phi + 1)

    def pt(r, phi, dz):
        a = phi + phase
        return (r * np.cos(a), r * np.sin(a), p.funnel_h + lead * phi / (2 * np.pi) + dz)

    for dz_off in (0.0, p.flight_t):
        for i in range(n_r):
            for j in range(n_phi):
                _quad(tris,
                      pt(rs[i], phis[j], dz_off), pt(rs[i + 1], phis[j], dz_off),
                      pt(rs[i + 1], phis[j + 1], dz_off), pt(rs[i], phis[j + 1], dz_off))
    # inner edge strip (skip when the flight is fused to a shaft)
    if p.shaft_r < r_in - 1e-9:
        for j in range(n_phi):
            _quad(tris,
                  pt(r_in, phis[j], 0.0), pt(r_in, phis[j + 1], 0.0),
                  pt(r_in, phis[j + 1], p.flight_t), pt(r_in, phis[j], p.flight_t))
    # radial end caps
    for phi in (phis[0], phis[-1]):
        for i in range(n_r):
            _quad(tris,
                  pt(rs[i], phi, 0.0), pt(rs[i + 1], phi, 0.0),
                  pt(rs[i + 1], phi, p.flight_t), pt(rs[i], phi, p.flight_t))
    return tris


def auger_triangles(p: AugerParams):
    tris = []
    # bore wall from the shelf to the top of the feed zone
    n_z = max(1, int(np.ceil((p.z_top - p.funnel_h) / p.dz)))
    tris += _surface_of_revolution(lambda s: p.bore_r, lambda s: s,
                                   np.linspace(p.funnel_h, p.z_top, n_z + 1), p.n_theta)
    # shelf annulus at the top of the cone
    if p.bore_r - p.funnel_top_r > 1e-6:
        tris += _surface_of_revolution(lambda s: s, lambda s: p.funnel_h,
                                       np.linspace(p.funnel_top_r, p.bore_r, 3), p.n_theta)
    # cone from the exit hole up to the shelf
    n_c = max(2, int(np.ceil(np.hypot(p.funnel_h, p.funnel_top_r - p.exit_r) / p.dz)))
    s = np.linspace(0.0, 1.0, n_c + 1)
    tris += _surface_of_revolution(lambda u: p.exit_r + u * (p.funnel_top_r - p.exit_r),
                                   lambda u: u * p.funnel_h, s, p.n_theta)
    # short exit throat (0.8 mm) so the hole has a rim, as printed
    tris += _surface_of_revolution(lambda u: p.exit_r, lambda u: u,
                                   np.linspace(-0.8, 0.0, 2), max(24, p.n_theta // 2))
    # flights
    for k in range(p.starts):
        tris += _helical_flight(p, 2 * np.pi * k / p.starts)
    # optional central shaft (closed at the bottom by the flight start / cone)
    if p.shaft_r > 0:
        tris += _surface_of_revolution(lambda s: p.shaft_r, lambda s: s,
                                       np.linspace(p.funnel_h, p.z_top, n_z + 1), p.n_theta // 2)
    return np.asarray(tris, dtype=float)


def write_ascii_stl(path: str, tris: np.ndarray, name: str = "auger") -> None:
    with open(path, "w") as f:
        f.write(f"solid {name}\n")
        for t in tris:
            n = np.cross(t[1] - t[0], t[2] - t[0])
            nn = np.linalg.norm(n)
            if nn < 1e-14:
                continue  # drop degenerate facets (LIGGGHTS rejects them)
            n = n / nn
            f.write(f" facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n  outer loop\n")
            for v in t:
                f.write(f"   vertex {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            f.write("  endloop\n endfacet\n")
        f.write(f"endsolid {name}\n")


def write_disk_stl(path: str, radius: float, z: float, n: int = 48) -> None:
    """Planar counting disk (normal -z) for fix massflow/mesh."""
    th = np.linspace(0, 2 * np.pi, n + 1)
    tris = [((0.0, 0.0, z), (radius * np.cos(th[j + 1]), radius * np.sin(th[j + 1]), z),
             (radius * np.cos(th[j]), radius * np.sin(th[j]), z)) for j in range(n)]
    write_ascii_stl(path, np.asarray(tris), "outlet")


def pocket_volume_mm3(p: AugerParams) -> float:
    """Free volume of one flight pocket (one pitch, one start)."""
    r_in = max(p.core_r, p.shaft_r)
    annulus = np.pi * (p.bore_r ** 2 - r_in ** 2)
    return annulus * (p.pitch - p.flight_t)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--params", default="{}", help="JSON dict overriding AugerParams")
    ap.add_argument("--out", default="auger.stl")
    ap.add_argument("--disk", default="outlet.stl")
    a = ap.parse_args()
    prm = AugerParams(**json.loads(a.params))
    T = auger_triangles(prm)
    write_ascii_stl(a.out, T)
    write_disk_stl(a.disk, radius=prm.exit_r + 6.0, z=-1.5)
    print(json.dumps({**asdict(prm), "n_tris": len(T), "z_top": prm.z_top,
                      "pocket_mm3": pocket_volume_mm3(prm)}))
