"""Interference check of each concept against the assembly (OCC booleans),
at tilt 0 and 45 deg, plus the auger lifted 45 mm out of its clips (swap).

    python3 check.py
"""
from __future__ import annotations

import sys

import cadquery as cq
import numpy as np
from OCP.gp import gp_Trsf

import concepts as C

C.ensure_pr170()
sys.path.insert(0, str(C.FA / "onshape"))
import layout  # noqa: E402

FIXED = ["Baseplate", "Servo MG996R (+X)", "Servo MG996R (-X)", "Servo pinion (+X)", "Servo pinion (-X)"]
ON_PLATE = ["Mounting plate", "Stepper (NEMA 11)", "Stepper pinion"]
TUBE = ["Auger", "Auger cap"]
_c: dict = {}


def moved(shape, M):
    tr = gp_Trsf()
    tr.SetValues(*M[0, :4], *M[1, :4], *M[2, :4])
    return cq.Shape.cast(shape.moved(cq.Location(tr)).wrapped)


def step(rel):
    if rel not in _c:
        _c[rel] = cq.Compound.makeCompound(cq.importers.importStep(str(C.FA / "components" / rel)).vals())
    return _c[rel]


def L_world(tilt):
    t = (layout.T(None, (0, layout.HINGE_Y, layout.HINGE_Z)) @ layout.rot_about(layout.X, tilt)
         @ layout.T(None, (0, -layout.HINGE_Y, -layout.HINGE_Z)))
    return t @ layout.MP @ layout.T(None, tuple(C.L2MP))


def check(k: int, tilt: float, lift: float = 0.0, saddle_open: float = 0.0) -> list:
    pl = layout.placements(tilt)
    up = layout.T(None, (0, 0, lift))
    others = {n: moved(step(pl[n][0]), pl[n][1]) for n in FIXED + ON_PLATE}
    others.update({n: moved(step(pl[n][0]), up @ pl[n][1]) for n in TUBE})
    Lw = L_world(tilt)
    rows = [-124.0 - C.TAP_ROW_MP_X] + ([] if k == 2 else [C.FRONT_BRACKET_X])
    for i, rx in enumerate(rows):
        others[f"Flexible bracket {i}"] = moved(C.bracket_in_L(rx).val(), Lw)
    parts = C.concept4(open_deg=saddle_open) if (k == 4 and saddle_open) else C.CONCEPTS[k][1]()
    if k == 2 and lift:
        # the tube has to snap out through the clip's lips, as with every Flexible
        # Bracket; check only the tower part of the tap bracket against the lift
        keep = C.box(C.FRONT_BRACKET_X + 6.0, 60.0, -60.0, 80.0, -80.0, 80.0)
        parts = {n: (w.intersect(keep) if "printed" in n else w) for n, w in parts.items()}
    mine = {n: moved(w.val(), Lw) for n, w in parts.items()}
    hits = []
    for a, sa in mine.items():
        for b, sb in others.items():
            v = sa.intersect(sb).Volume()
            if v > 0.05:
                hits.append((a, b, round(v, 2)))
    return hits


LIFTS = (5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0)


def sweep(k: int, saddle_open: float = 0.0) -> list:
    """Overlaps while the auger is lifted out of its clips, 5..50 mm."""
    out = []
    for lift in LIFTS:
        hits = [h for h in check(k, 0.0, lift, saddle_open) if h[1] in TUBE]
        out += [(lift, *h) for h in hits]
    return out


if __name__ == "__main__":
    for k in (1, 2, 3, 4):
        for tilt in (0.0, 45.0):
            hits = check(k, tilt)
            print(f"concept {k}, tilt {tilt:g}: " + ("no overlaps" if not hits else str(hits)))
        hits = sweep(k)
        note = " (tower; the clip itself snaps open like any Flexible Bracket)" if k == 2 else ""
        print(f"concept {k}, auger lifted 5-50 mm{note}: " + ("clear at every step" if not hits
                                                               else f"blocked, e.g. {hits[0]}"))
    hits = sweep(4, saddle_open=75.0)
    print("concept 4, saddle flipped open 75 deg, auger lifted 5-50 mm: "
          + ("clear at every step" if not hits else f"blocked, e.g. {hits[0]}"))
