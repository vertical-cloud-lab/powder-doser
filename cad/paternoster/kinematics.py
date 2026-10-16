"""Exact chain kinematics for the paternoster loop.

Both chains are identical and in step (the bottom corner shafts carry the
front and back sprockets), so everything is solved once in the chain plane
(y, z) and used at x = 0 (front) and x = CHAIN_L (back).

The loop runs counter-clockwise in (y, z): bottom run toward +y, up the
right side, top run toward -y, down the left side. A point on the loop is
given by u, in links, measured from where the chain leaves the bottom-left
sprocket onto the bottom run. Segment by segment:

    bottom run  [0, 20]    bottom-right corner [20, 28]
    right side  [28, 52]   top-right corner    [52, 60]
    top run     [60, 80]   top-left corner     [80, 88]
    left side   [88, 112]  bottom-left corner  [112, 120]

All four sprockets turn by one tooth per link of travel. Pins on a sprocket
sit exactly in its seats; the free spans are straight between the last pin
seated on one sprocket and the first on the next (polygonal action: the
spans rise and fall by R(1 - cos(pi/32)) = 0.23 mm). Every span is a whole
number of pitches, so this is exact, not an approximation.

`shift` s is the chain's travel in links. Pin j sits at u = j + s (mod 120).
Module k hangs from the SA-1 link whose pins are j = 10k and 10k + 1. At
s = HOME_SHIFT module 0's link is centred on the station (u = 10).
"""
from __future__ import annotations

import math

import numpy as np

from params import (CORNER_Y, LOOP_M, LOOP_N, MODULE_LINKS, N_LINKS, N_MODULES, N_TEETH, P, R, SA1_C,
                    STATION_U, Z_BOT, Z_TOP)

DELTA = 2 * math.pi / N_TEETH
HOME_SHIFT = STATION_U - 0.5          # the link from u = 9.5 to 10.5 is centred on the station

# corners in travel order after each straight: (centre (y, z), arrival angle)
# arrival angle = where the chain meets the sprocket; it leaves 90 deg later.
CORNERS = [
    ((CORNER_Y, Z_BOT), -math.pi / 2),      # bottom-right: arrives at the bottom, leaves at the right
    ((CORNER_Y, Z_TOP), 0.0),               # top-right
    ((-CORNER_Y, Z_TOP), math.pi / 2),      # top-left
    ((-CORNER_Y, Z_BOT), math.pi),          # bottom-left
]
STRAIGHTS = [LOOP_M, LOOP_N, LOOP_M, LOOP_N]   # straight before each corner, in links
WRAP = N_TEETH // 4                            # 8 links per 90 deg corner
SEG_START = []                                 # u where each straight starts
_u = 0.0
for k in range(4):
    SEG_START.append(_u)
    _u += STRAIGHTS[k] + WRAP
assert abs(_u - N_LINKS) < 1e-9


def _seat(c: int, ang: float) -> np.ndarray:
    (cy, cz), _ = CORNERS[c]
    return np.array([cy + R * math.cos(ang), cz + R * math.sin(ang)])


def pin_positions(shift: float) -> np.ndarray:
    """(N_LINKS, 2) array of pin centres (y, z); pin j at u = j + shift.

    All four sprockets turn together, so every free span leaves one sprocket and
    meets the next at the same tooth phase g in [-1/2, 1/2) of a tooth: its end pins
    sit at (departure angle + g*DELTA) and (arrival angle + g*DELTA), exactly a
    whole number of pitches apart, and the span rides up and down by
    R(1 - cos(DELTA/2)). When g passes +1/2 the next pin takes over as the end pin;
    at that instant it is already on both the span and the seat, so nothing jumps."""
    f = shift - math.floor(shift)
    g = f if f < 0.5 else f - 1.0
    out = np.zeros((N_LINKS, 2))
    for j in range(N_LINKS):
        v = (j + shift - g) % N_LINKS              # pin's place in the nominal (g = 0) layout
        for k in range(4):
            a, n = SEG_START[k], STRAIGHTS[k]
            prev_c = (k - 1) % 4
            if a - 1e-9 <= v <= a + n + 1e-9:
                pa = _seat(prev_c, CORNERS[prev_c][1] + math.pi / 2 + g * DELTA)
                pb = _seat(k, CORNERS[k][1] + g * DELTA)
                out[j] = pa + (v - a) / n * (pb - pa)
                break
            if a + n < v < a + n + WRAP + 1e-9:
                out[j] = _seat(k, CORNERS[k][1] + (v - (a + n) + g) * DELTA)
                break
        else:
            raise RuntimeError(f"pin {j} at v={v} not placed")
    return out


def link_frames(shift: float) -> list[tuple[np.ndarray, float]]:
    """For link j (pins j, j+1): (midpoint (y, z), angle of travel direction in the yz plane)."""
    p = pin_positions(shift)
    q = np.roll(p, -1, axis=0)
    mids = (p + q) / 2
    ang = np.arctan2(q[:, 1] - p[:, 1], q[:, 0] - p[:, 0])
    return [(mids[j], float(ang[j])) for j in range(N_LINKS)]


def module_link(k: int) -> int:
    """Index of the first pin of module k's SA-1 link (an outer link: even j)."""
    return (MODULE_LINKS * k) % N_LINKS


def pivots(shift: float) -> np.ndarray:
    """(N_MODULES, 2) pivot centres (y, z): link midpoint + C1 along the outward normal."""
    p = pin_positions(shift)
    out = np.zeros((N_MODULES, 2))
    for k in range(N_MODULES):
        j = module_link(k)
        a, b = p[j], p[(j + 1) % N_LINKS]
        t = (b - a) / np.linalg.norm(b - a)
        nrm = np.array([t[1], -t[0]])         # outward for a counter-clockwise loop
        out[k] = (a + b) / 2 + SA1_C * nrm
    return out


def tab_angle(shift: float, k: int) -> float:
    """Travel-direction angle of module k's SA-1 link (the tab is square to it)."""
    p = pin_positions(shift)
    j = module_link(k)
    a, b = p[j], p[(j + 1) % N_LINKS]
    return math.atan2(b[1] - a[1], b[0] - a[0])


def sprocket_angle(shift: float) -> float:
    """Rotation of every corner sprocket (counter-clockwise in yz) for a given shift."""
    return shift * DELTA


def station_shift(k: int) -> float:
    """Chain shift that puts module k at the station."""
    return (HOME_SHIFT - MODULE_LINKS * k) % N_LINKS


def load_shift(k: int) -> float:
    """Chain shift that puts module k at the loading position (right side, mid-height)."""
    return (station_shift(k) + 3 * MODULE_LINKS) % N_LINKS


if __name__ == "__main__":
    for s in (HOME_SHIFT, HOME_SHIFT + 0.37, HOME_SHIFT + 5.0):
        p = pin_positions(s)
        d = np.linalg.norm(np.roll(p, -1, axis=0) - p, axis=1)
        print(f"shift {s:7.3f}: pitch min {d.min():.4f} max {d.max():.4f}")
    pv = pivots(HOME_SHIFT)
    print("module 0 pivot at home:", pv[0].round(3), " module 3:", pv[3].round(3))
