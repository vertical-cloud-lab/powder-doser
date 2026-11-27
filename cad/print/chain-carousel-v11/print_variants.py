"""Print-only variants of chain-carousel-v11's printed parts (export_printed.py imports this with cad/chain-carousel-v11 on the path).

The v11 CAD (cad/chain-carousel-v11/*.py) is not changed: each function builds the part from v11's own builders and makes only the
change printing needs, and each is listed, with the CAD fix it stands for, in ../README.md ("chain-carousel-v11").

* carriage(): the assembly's carriage with its print webs (parts.tab_hook's 0.8 mm break-off webs), as v11's build.py exports it.
* latch_bolt(): parts7.latch_bolt_v7 is the steel dowel fused to the printed carrier (pin.union(carrier)) for the assembly; the printed
  part is the carrier and its rest shelf with the dowel's 4.0 mm hole, 2 mm deep, where the dowel is pressed in (v11's build.py has
  exported the same since 2026-11-27).
* hatch_knob(): the knob parts3.hatch_door puts on the side hatch's acrylic door (printed, bonded to the acrylic).

(The T-bracket's variant, its head joined to its stem, went when parts11.t_bracket_v11 was fixed on 2026-11-27.)
"""
from __future__ import annotations

import cadquery as cq

import layout as L
import parts7 as P7
import parts11 as P11
from params import KEEPER6_X, LATCH6_ENGAGE, LATCH6_PIN, LATCH_Y6
from parts6 import _cyl_x


def _one(w: cq.Workplane) -> cq.Shape:
    vals = w.vals()
    return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)


def carriage() -> cq.Shape:
    return _one(P11.carriage_v11(print_web=True))


def latch_bolt() -> cq.Shape:
    d, _, zp = LATCH6_PIN
    tip = KEEPER6_X[1] - LATCH6_ENGAGE
    c0 = P7.LATCH7_CARRIER[0]
    return _one(P7.latch_bolt_v7().cut(_cyl_x(d / 2, tip - 1.0, c0 + 2.0, LATCH_Y6, zp)))


def hatch_knob() -> cq.Shape:
    door = cq.Workplane("XY").add(L.shape("hatch_side"))
    return _one(door.intersect(cq.Workplane("XY").box(2000, 2000, 100, centered=(True, True, False)).translate((0, 0, L.ACRYLIC_T))))
