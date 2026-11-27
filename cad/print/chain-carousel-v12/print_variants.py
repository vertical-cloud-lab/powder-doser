"""Print-only variants of chain-carousel-v12's printed parts (export_printed.py imports this with cad/chain-carousel-v12 on the path).

v12 keeps v11's carriage, latch bolt and side hatch, so these are v11's three variants (../chain-carousel-v11/print_variants.py),
built from v12's own modules. The v12 CAD (cad/chain-carousel-v12/*.py) is not changed: each function builds the part from v12's
builders and makes only the change printing needs.

* carriage(): the assembly's carriage with its print webs (parts.tab_hook's 0.8 mm break-off webs), as v12's build.py exports it.
* latch_bolt(): parts7.latch_bolt_v7 is the steel dowel fused to the printed carrier (pin.union(carrier)) for the assembly; the printed
  part is the carrier and its rest shelf with the dowel's 4.0 mm hole, 2 mm deep, where the dowel is pressed in (as v12's build.py).
* hatch_knob(): the knob parts3.hatch_door puts on the side hatch's acrylic door (printed, bonded to the acrylic).

EC v12, the pinion cradle and the second guide are printed as the CAD draws them (layout.shape), so they have no variant here.
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
