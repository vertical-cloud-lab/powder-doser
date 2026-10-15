"""Fasteners for the powder-doser assemblies: step.parts geometry in PR #170's seat frames.

``fastener(kind)`` returns one fastener as build123d geometry, read from a
vendor STEP under ``STEP/imported/`` and re-framed into the local "seat"
frame that PR #170's ``cad/full-assembly/hardware.py`` uses for the same
part (and that its stand-ins ``components/hardware/<kind>.step`` are drawn
in), so the 4 x 4 transforms of ``hardware.fastener_placements()`` place
these parts unchanged.

Seat frame (mm), as measured on every PR #170 stand-in:

* the fastener axis is +Z through the origin, +Z pointing the way the screw
  goes in (for a nut or standoff: away from the part it bears on);
* socket, button and pan head screws: bearing face (head underside) on
  z = 0, head in z < 0, shank in 0 <= z <= L;
* flat (90 deg countersunk) head screw: the flush head top on z = 0, head
  cone and shank in 0 <= z <= L (L is overall length, as McMaster quotes it);
* nuts: bearing face on z = 0, nut in 0 <= z <= m (a nylon-insert crown is
  at the z = m end); hex corners on +-X, flats facing +-Y;
* standoff (no PR #170 stand-in; same convention as a nut): 0 <= z <= L,
  hex corners on +-X.

step.parts STEPs put the bearing face on z = 0 too, but with the shank
along -Z, so screws are turned 180 deg about X; nuts come with their
corners on +-Y and are turned 30 deg about Z.  Per kind:

==================  =========  =================================================  ======================
kind                McMaster   source (STEP/imported/...)                         re-frame
==================  =========  =================================================  ======================
bhcs_m5x45          92095A223  step-parts/button_head_screw_m5_l0050_simple       shank cut to 45, Rx 180
locknut_m5          93625A200  pr170-hardware/locknut_m5 (PR #170 stand-in)       none
shcs_m3x14          91292A027  step-parts/iso4762_socket_head_cap_screw_m3x14     Rx 180
locknut_m3          93625A100  step-parts/nyloc_nut_m3                            Rz 30
hexnut_m3           91828A211  step-parts/iso4032_hex_nut_m3                      Rz 30
shcs_m3x10          91292A113  step-parts/iso4762_socket_head_cap_screw_m3x10     Rx 180
bhcs_m3x20          92095A185  step-parts/button_head_screw_m3_l0020_simple       Rx 180
bhcs_m3x25          92095A186  step-parts/button_head_screw_m3_l0025_simple       Rx 180
fhcs_m3x30          92125A140  step-parts/countersunk_socket_screw_m3_l0030_simple  Rx 180
shcs_m3x5           91292A110  step-parts/socket_head_cap_screw_m3_l0005_simple   Rx 180
shcs_m2p5x8         91292A012  step-parts/iso4762_socket_head_cap_screw_m2p5x8    Rx 180
wood_10x1p25        93360A609  pr170-hardware/wood_10x1p25 (PR #170 stand-in)     none
shcs_m3x12          -          step-parts/iso4762_socket_head_cap_screw_m3x12     Rx 180
shcs_m3x6           -          step-parts/iso4762_socket_head_cap_screw_m3x6      Rx 180
standoff_m3x10_ff   -          step-parts/standoff_hex_female_female_m3_l0010_simple  none
==================  =========  =================================================  ======================

Fallbacks and caveats (details, queries and measurements in
``checks/results/fasteners_step_parts.json``):

* step.parts has no M5 x 45 button head (ISO 7380 M5 comes in 40 and 50), so
  ``bhcs_m5x45`` is its M5 x 50 with the shank cut at 45 mm.  That shank is
  a plain flat-ended cylinder, so the cut end is the same as the vendor's.
* step.parts' only M5 nylon-insert locknut (``nylon_locknut_m5_simple``) is
  a plain 8 x 4.0 mm hex prism, against McMaster's 8 x 5 mm nylon-insert
  nut, so ``locknut_m5`` stays PR #170's stand-in.  step.parts has no wood
  or pan head screw at all, so neither does ``wood_10x1p25``.
* The "_simple" step.parts screws draw the thread as a plain shank at the
  basic minor diameter (M3: 2.459, M5: 4.134 mm), not the major diameter.

Usage::

    from lib.fasteners import fastener, MCMASTER_KIND
    screw = fastener("shcs_m3x10")                 # seat frame
    nut = fastener(MCMASTER_KIND["93625A100"])     # M3 nylon-insert locknut
    placed = screw.moved(bd.Location(...))         # world placement

Every call reads its STEP through ``cadgen.read_step`` (a warm store read
is tens of milliseconds), so the file is recorded as an input of whatever
build calls it; nothing is cached at module level.  For many copies of
one kind, call ``fastener`` once and place the result with ``moved``.
"""
from __future__ import annotations

from pathlib import Path

from cadgen import build123d as bd
from cadgen import read_step

_IMPORTED = Path(__file__).resolve().parents[2] / "STEP" / "imported"

STEEL = (0.74, 0.75, 0.77)      # 18-8 / 316 stainless
NYLON = (0.93, 0.92, 0.86)      # nylon insert ring

# kind -> source and re-frame.  "flip": turn 180 deg about X (step.parts
# screws have the shank along -Z); "rot_z_deg": then turn about Z (puts nut
# corners on +-X); "trim_length": keep only vendor z >= -trim_length (a
# shorter screw from a longer one); "insert": the smaller solids are the
# nylon insert.
FASTENERS: dict[str, dict] = {
    "bhcs_m5x45": {
        "desc": "M5 x 45 button head hex-drive screw (ISO 7380), 18-8 stainless",
        "mcmaster": "92095A223",
        "file": "step-parts/button_head_screw_m5_l0050_simple.step",
        "flip": True, "rot_z_deg": 0.0, "trim_length": 45.0,
    },
    "locknut_m5": {
        "desc": "M5 nylon-insert locknut, 18-8 stainless (PR #170 stand-in)",
        "mcmaster": "93625A200",
        "file": "pr170-hardware/locknut_m5.step",
        "flip": False, "rot_z_deg": 0.0,
    },
    "shcs_m3x14": {
        "desc": "M3 x 14 socket head screw (ISO 4762), 18-8 stainless",
        "mcmaster": "91292A027",
        "file": "step-parts/iso4762_socket_head_cap_screw_m3x14.step",
        "flip": True, "rot_z_deg": 0.0,
    },
    "locknut_m3": {
        "desc": "M3 nylon-insert locknut, 18-8 stainless",
        "mcmaster": "93625A100",
        "file": "step-parts/nyloc_nut_m3.step",
        "flip": False, "rot_z_deg": 30.0, "insert": True,
    },
    "hexnut_m3": {
        "desc": "M3 hex nut (ISO 4032 / DIN 934), 18-8 stainless",
        "mcmaster": "91828A211",
        "file": "step-parts/iso4032_hex_nut_m3.step",
        "flip": False, "rot_z_deg": 30.0,
    },
    "shcs_m3x10": {
        "desc": "M3 x 10 socket head screw (ISO 4762), 18-8 stainless",
        "mcmaster": "91292A113",
        "file": "step-parts/iso4762_socket_head_cap_screw_m3x10.step",
        "flip": True, "rot_z_deg": 0.0,
    },
    "bhcs_m3x20": {
        "desc": "M3 x 20 button head hex-drive screw (ISO 7380), 18-8 stainless",
        "mcmaster": "92095A185",
        "file": "step-parts/button_head_screw_m3_l0020_simple.step",
        "flip": True, "rot_z_deg": 0.0,
    },
    "bhcs_m3x25": {
        "desc": "M3 x 25 button head hex-drive screw (ISO 7380), 18-8 stainless",
        "mcmaster": "92095A186",
        "file": "step-parts/button_head_screw_m3_l0025_simple.step",
        "flip": True, "rot_z_deg": 0.0,
    },
    "fhcs_m3x30": {
        "desc": "M3 x 30 flat head hex-drive screw, 90 deg (ISO 10642), 18-8 stainless",
        "mcmaster": "92125A140",
        "file": "step-parts/countersunk_socket_screw_m3_l0030_simple.step",
        "flip": True, "rot_z_deg": 0.0,
    },
    "shcs_m3x5": {
        "desc": "M3 x 5 socket head screw (ISO 4762), 18-8 stainless",
        "mcmaster": "91292A110",
        "file": "step-parts/socket_head_cap_screw_m3_l0005_simple.step",
        "flip": True, "rot_z_deg": 0.0,
    },
    "shcs_m2p5x8": {
        "desc": "M2.5 x 8 socket head screw (ISO 4762), 18-8 stainless",
        "mcmaster": "91292A012",
        "file": "step-parts/iso4762_socket_head_cap_screw_m2p5x8.step",
        "flip": True, "rot_z_deg": 0.0,
    },
    "wood_10x1p25": {
        "desc": "#10 x 1-1/4 in pan head Phillips wood screw, 316 stainless (PR #170 stand-in)",
        "mcmaster": "93360A609",
        "file": "pr170-hardware/wood_10x1p25.step",
        "flip": False, "rot_z_deg": 0.0,
    },
    "shcs_m3x12": {
        "desc": "M3 x 12 socket head screw (ISO 4762)",
        "mcmaster": None,
        "file": "step-parts/iso4762_socket_head_cap_screw_m3x12.step",
        "flip": True, "rot_z_deg": 0.0,
    },
    "shcs_m3x6": {
        "desc": "M3 x 6 socket head screw (ISO 4762), for the PCB",
        "mcmaster": None,
        "file": "step-parts/iso4762_socket_head_cap_screw_m3x6.step",
        "flip": True, "rot_z_deg": 0.0,
    },
    "standoff_m3x10_ff": {
        "desc": "M3 x 10 mm hex standoff, female-female (7.5 mm across flats), for the PCB",
        "mcmaster": None,
        "file": "step-parts/standoff_hex_female_female_m3_l0010_simple.step",
        "flip": False, "rot_z_deg": 0.0,
    },
}

# McMaster-Carr part number -> kind (PR #170's fastener table)
MCMASTER_KIND: dict[str, str] = {
    "92095A223": "bhcs_m5x45",
    "93625A200": "locknut_m5",
    "91292A027": "shcs_m3x14",
    "93625A100": "locknut_m3",
    "91828A211": "hexnut_m3",
    "91292A113": "shcs_m3x10",
    "92095A185": "bhcs_m3x20",
    "92095A186": "bhcs_m3x25",
    "92125A140": "fhcs_m3x30",
    "91292A110": "shcs_m3x5",
    "91292A012": "shcs_m2p5x8",
    "93360A609": "wood_10x1p25",
}


def source_path(kind: str) -> Path:
    """The vendor STEP ``fastener(kind)`` reads."""
    return _IMPORTED / _spec(kind)["file"]


def _spec(kind: str) -> dict:
    try:
        return FASTENERS[kind]
    except KeyError:
        raise KeyError(f"unknown fastener kind {kind!r}; known: {', '.join(FASTENERS)}") from None


def fastener(kind: str) -> bd.Shape:
    """One fastener of ``kind`` (a key of FASTENERS) in its seat frame (see
    the module docstring), labelled ``kind`` and coloured stainless."""
    spec = _spec(kind)
    shape = read_step(source_path(kind))
    if spec.get("trim_length"):
        keep = bd.Pos(0, 0, -spec["trim_length"]) * bd.Box(
            1000, 1000, 1000, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        shape = shape & keep
    loc = bd.Rot(0, 0, spec["rot_z_deg"]) * (bd.Rot(180, 0, 0) if spec["flip"] else bd.Location())
    solids = sorted(shape.solids(), key=lambda s: -s.volume)
    if len(solids) == 1:
        out = solids[0].moved(loc)
        out.label, out.color = kind, bd.Color(*STEEL)
        return out
    parts = []
    for i, s in enumerate(solids):
        p = s.moved(loc)
        insert = bool(spec.get("insert")) and i > 0
        p.label = "nylon_insert" if insert else ("body" if i == 0 else f"body_{i}")
        p.color = bd.Color(*(NYLON if insert else STEEL))
        parts.append(p)
    return bd.Compound(children=parts, label=kind)
