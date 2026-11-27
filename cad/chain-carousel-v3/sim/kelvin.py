"""Shared models for the v3 and v4 station sims (no imports from the CAD, so v3 and v4 can both load it).

* Seat magnet: K&J D44-N52 (1/4 x 1/4 in) pulling a 1/4 in chrome-steel ball.
  - The magnet is two uniformly charged discs (sigma = +-Br/mu0, Br 1.45 T), integrated numerically.
  - The ball is soft iron, each small cell magnetised as a sphere in the local field would be,
    M = 3 H0 (the high-permeability limit), capped at saturation (1.7 T for hardened 52100).
  - Pull = d/dz of the co-energy integral over the ball's cells.
  - Check: the same magnet on a thick ideal-iron plate (image method, exact for coaxial discs) against
    K&J's published "case 1" pull, 4.15 lb (18.5 N).
* Kelvin clamp statics: the EC on the plate through a cone (3 unknowns), a vee (2) and a flat (1).
  That is exactly six contacts, so the contact forces follow from the six equilibrium equations.
  Frictionless contacts give the conservative (earliest) opening.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import integrate, special

MU0 = 4e-7 * math.pi
BR = 1.45            # T, N52 (K&J lists Br max 1.48 T)
JS = 1.7             # T, saturation of hardened 52100 (about 1.6-1.8 T)
A_MAG, H_MAG = 3.175e-3, 6.35e-3
R_BALL = 3.175e-3
KJ_CASE1_N = 4.15 * 4.448     # K&J D44-N52 pull force, case 1 (magnet on a thick steel plate)


# ----------------------------------------------------------------------------------------------- magnet model
def _disc_nodes(a=A_MAG, nr=28, nphi=72):
    xr, wr = np.polynomial.legendre.leggauss(nr)
    r = 0.5 * a * (xr + 1.0)
    wr = 0.5 * a * wr * r
    ph = (np.arange(nphi) + 0.5) * 2 * math.pi / nphi
    R, P = np.meshgrid(r, ph, indexing="ij")
    w = (wr[:, None] * np.full(nphi, 2 * math.pi / nphi)[None, :]).ravel()
    return np.c_[(R * np.cos(P)).ravel(), (R * np.sin(P)).ravel()], w


_NODES = _disc_nodes()


def h_cylinder(pts, br=BR):
    """H (A/m) of an axially magnetised cylinder with its north face at z = 0 and its south face at z = -H_MAG."""
    xy, w = _NODES
    sig = br / MU0
    H = np.zeros_like(pts)
    for z0, s in ((0.0, 1.0), (-H_MAG, -1.0)):
        src = np.c_[xy, np.full(len(w), z0)]
        for i in range(0, len(pts), 800):
            d = pts[i:i + 800, None, :] - src[None]
            r2 = np.einsum("ijk,ijk->ij", d, d)
            H[i:i + 800] += s * sig / (4 * math.pi) * np.einsum("ijk,ij->ik", d, w / r2 ** 1.5)
    return H


def _ball_cells(step=0.3e-3):
    g = np.arange(-R_BALL + step / 2, R_BALL, step)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    p = np.c_[X.ravel(), Y.ravel(), Z.ravel()]
    p = p[(p ** 2).sum(1) <= R_BALL ** 2]
    return p, step ** 3


_CELLS = _ball_cells()


def _coenergy(Hmag, chi=3.0, js=JS):
    ms = js / MU0
    hk = ms / chi
    lin = MU0 * chi * Hmag ** 2 / 2
    sat = MU0 * (ms * hk / 2 + ms * (Hmag - hk))
    return np.where(Hmag <= hk, lin, sat)


def ball_pull(gap_m, offset_m=0.0, js=JS, dz=0.02e-3):
    """Pull (N, toward the magnet) on the ball whose lowest point is gap_m above the magnet's face, offset_m off its axis."""
    cells, dv = _CELLS
    W = []
    for s in (-1, 1):
        c = np.array([offset_m, 0.0, gap_m + R_BALL + s * dz])
        H = h_cylinder(cells + c)
        W.append(_coenergy(np.linalg.norm(H, axis=1), js=js).sum() * dv)
    return -(W[1] - W[0]) / (2 * dz)


def _I(s):
    if s == 0:
        return 0.5
    f = lambda x: special.j1(x) ** 2 * math.exp(-s * x) / x
    return integrate.quad(f, 0, 60.0 / s + 60.0, limit=400)[0]


def case1_pull(gap_m, br=BR):
    """Magnet on an ideal (infinitely permeable, unsaturated) thick plate at gap_m: the magnet and its image."""
    a, h = A_MAG, H_MAG
    k = math.pi * br ** 2 * a ** 2 / MU0
    return k * (_I(2 * gap_m / a) - 2 * _I((2 * gap_m + h) / a) + _I((2 * gap_m + 2 * h) / a))


def em_pull(gap_mm):
    """Adafruit 3872 on a 2 mm armature, v2's law: 20 N / (1 + g / 0.4 mm)^2 (10.6 N at 0.15 mm)."""
    return 20.0 / (1.0 + max(gap_mm, 0.0) / 0.4) ** 2


# ----------------------------------------------------------------------------------------------- Kelvin statics
def kelvin_solve(R, t, geom, loads, pivot):
    """Contact forces on the EC (frame coordinates) for the loads [(point_sam, force_frame)] on the EC.

    R, t: Sam's (module) frame -> frame. geom: A, B, C (contact points, Sam frame), axis (unit, from the EC toward the plate,
    Sam frame), vee (two unit directions of the force on the EC from ball B, Sam frame), c_dir (force on the EC at C per
    unit normal, Sam frame). Returns dict with fA (3), N1, N2, NC."""
    W = lambda p: R @ np.asarray(p, float) + t
    pA, pB, pC = W(geom["A"]), W(geom["B"]), W(geom["C"])
    dirs = [np.eye(3)[0], np.eye(3)[1], np.eye(3)[2], R @ geom["vee"][0], R @ geom["vee"][1], R @ geom["c_dir"]]
    pts = [pA, pA, pA, pB, pB, pC]
    A = np.zeros((6, 6))
    for j, (d, p) in enumerate(zip(dirs, pts)):
        A[:3, j] = d
        A[3:, j] = np.cross(p - pivot, d)
    b = np.zeros(6)
    for p, f in loads:
        p = W(p)
        b[:3] -= f
        b[3:] -= np.cross(p - pivot, f)
    x = np.linalg.solve(A, b)
    return x


def kelvin_check(x, R, geom, cone_half=45.0, mu=0.0):
    """Margins (>= 0 holds) for a solution: cone (ball inside its friction cone), vee normals, flat normal."""
    a = R @ geom["axis"]
    g = -x[:3]                                    # force on ball A from the cone
    ax = g @ a
    perp = np.linalg.norm(g - ax * a)
    lim = math.tan(math.radians(90.0 - cone_half) + math.atan(mu))
    return dict(cone_axial=ax, cone_slip=ax * lim - perp, vee1=x[3], vee2=x[4], flat=x[5])


def _generators(R, geom, mu_cone, mu_steel, cone_half=45.0, ncone=8):
    """Unit force generators on the EC (frame) and their points (Sam), for the friction LP."""
    a = R @ geom["axis"]
    e1 = R @ np.array([1.0, 0, 0]) if abs(geom["axis"][0]) < 0.9 else R @ np.array([0, 1.0, 0])
    e1 = e1 - (e1 @ a) * a
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(a, e1)
    beta = math.radians(90.0 - cone_half) + math.atan(mu_cone)
    beta = min(beta, math.radians(89.9))
    gens = []
    for k in range(ncone):
        ph = 2 * math.pi * k / ncone
        gens.append((geom["A"], -(math.cos(beta) * a + math.sin(beta) * (math.cos(ph) * e1 + math.sin(ph) * e2))))
    yax = R @ np.array([0, 1.0, 0])
    for v in geom["vee"]:
        n = -(R @ v)                                   # force on the ball from the dowel
        t2 = np.cross(n, yax)
        t2 /= np.linalg.norm(t2)
        for t in (yax, -yax, t2, -t2):
            gens.append((geom["B"], -(n + mu_steel * t)))
    c = R @ geom["c_dir"]
    tx = R @ np.array([1.0, 0, 0])
    for t in (tx, -tx, yax, -yax):
        gens.append((geom["C"], c + mu_steel * t))
    return gens


def lp_holds(R, t, geom, loads, pivot, mu_cone, mu_steel):
    """True if some set of contact forces inside the friction cones balances the loads (best case for a frictional dock)."""
    from scipy.optimize import linprog
    W = lambda p: R @ np.asarray(p, float) + t
    gens = _generators(R, geom, mu_cone, mu_steel)
    A = np.zeros((6, len(gens)))
    for j, (p, d) in enumerate(gens):
        A[:3, j] = d
        A[3:, j] = np.cross(W(p) - pivot, d)
    b = np.zeros(6)
    for p, f in loads:
        p = W(p)
        b[:3] -= f
        b[3:] -= np.cross(p - pivot, f)
    r = linprog(np.zeros(len(gens)), A_eq=A, b_eq=b, bounds=(0, None), method="highs")
    return r.status == 0
