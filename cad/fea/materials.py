"""Materials for the FEA (mm, N, MPa, t/mm^3) and the allowable stress each part is checked against.

allow is what a safety factor is measured against: tensile yield for the metals; for printed PETG the
datasheet's tensile strength ACROSS the layers (Z), because a print fails between layers first and most of
these parts carry bending across them somewhere; a sustained load is checked against a creep allowable.

Sources:
  PETG: Bambu Lab PETG HF datasheet (ISO 527, 100 % infill): E 1810 +-190 MPa (X-Y), 1540 +-130 MPa (Z);
        tensile strength 34 +-4 MPa (X-Y), 23 +-4 MPa (Z). Creep: about 0.6 E after 1000 h at 20 % of
        strength is typical of PETG (no Bambu creep data), so the sustained-load runs use 1000 MPa.
  6061-T6: ASM / MatWeb, E 68.9 GPa, yield 276 MPa (ASTM B209 minimum 241 MPa for plate: used).
  1018 cold-drawn keyed shafting: E 205 GPa, yield 370 MPa.  1045 rod (idler axles): yield 310 MPa (hot-rolled minimum).
  18-8 stainless (shoulder screws, pins): E 193 GPa, yield 205 MPa (annealed minimum; screws are stronger).
  2020 extrusion (6063-T5/6105-T5 class): E 68.9 GPa, yield 145 MPa (6063-T5 minimum).
  UHMW-PE: E 690 MPa, yield 21 MPa.  Low-carbon steel sheet (1008/1010 CR): E 200 GPa, yield 180 MPa.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Material:
    key: str
    E: float
    nu: float
    rho: float
    allow: float
    label: str
    ortho: dict | None = None


_M = {
    "AL6061": Material("AL6061", 68900.0, 0.33, 2.70e-9, 241.0, "6061-T6 plate"),
    "AL6063": Material("AL6063", 68900.0, 0.33, 2.70e-9, 145.0, "2020 extrusion (6063-T5)"),
    "STEEL1018": Material("STEEL1018", 205000.0, 0.29, 7.87e-9, 370.0, "1018 CD steel"),
    "STEEL1045": Material("STEEL1045", 205000.0, 0.29, 7.85e-9, 310.0, "1045 steel"),
    "SS188": Material("SS188", 193000.0, 0.29, 8.00e-9, 205.0, "18-8 stainless"),
    "STEEL_LC": Material("STEEL_LC", 200000.0, 0.29, 7.87e-9, 180.0, "low-carbon steel sheet"),
    "STEEL_HARD": Material("STEEL_HARD", 205000.0, 0.29, 7.85e-9, 1000.0, "hardened steel dowel"),
    "PETG": Material("PETG", 1810.0, 0.38, 1.27e-9, 23.0, "PETG (printed, short-term)"),
    "PETG_CREEP": Material("PETG_CREEP", 1000.0, 0.38, 1.27e-9, 8.0, "PETG (printed, 1000 h creep)"),
    "UHMW": Material("UHMW", 690.0, 0.46, 0.94e-9, 21.0, "UHMW-PE"),
    "BRONZE": Material("BRONZE", 100000.0, 0.34, 8.80e-9, 100.0, "SAE 841 sintered bronze"),
    "RIGIDISH": Material("RIGIDISH", 205000.0, 0.29, 1.0e-12, 1e9, "massless stiff proxy"),
}


def get(key: str) -> Material:
    return _M[key]


def add(m: Material) -> Material:
    _M[m.key] = m
    return m


def equivalent_bar(key: str, EI: float, GJ: float, mass_per_mm: float, side: float = 20.0, allow: float = 145.0,
                   label: str = "") -> Material:
    """A solid side x side bar whose bending stiffness EI, torsional stiffness GJ and mass per length match a
    real section (the 2020 extrusion): orthotropic, axis = local x (set the part's orientation)."""
    I_bar = side ** 4 / 12.0
    J_bar = 0.1406 * side ** 4
    E1 = EI / I_bar
    G = GJ / J_bar
    rho = mass_per_mm / side ** 2
    o = dict(E1=E1, E2=E1, E3=E1, nu12=0.3, nu13=0.3, nu23=0.3, G12=G, G13=G, G23=E1 / 2.6)
    return add(Material(key, E1, 0.3, rho, allow, label or "equivalent bar", ortho=o))
