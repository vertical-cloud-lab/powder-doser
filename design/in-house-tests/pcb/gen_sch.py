#!/usr/bin/env python3
"""Generate fc1.kicad_sch (KiCad 9) from fc1_design.py.

Every pin gets a short wire stub ending in a net label, so connectivity is by
label name; symbols are copied (flattened) from the installed KiCad libraries,
plus the Coto 9002 relay from the project library fc1.kicad_sym.
Run: python3 gen_sch.py   (then kicad-cli sch erc fc1.kicad_sch)
"""
import copy
import os
import uuid

from sexp import parse, dumps, find, findall, Q
import fc1_design as D

HERE = os.path.dirname(os.path.abspath(__file__))
SYMDIR = "/usr/share/kicad/symbols/"
NS = uuid.UUID("6f1c2a52-6a1e-4c47-9a57-fc1fc1fc1fc1")
ROOT_UUID = str(uuid.uuid5(NS, "root-sheet"))


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


_libcache = {}


def load_lib(lib):
    if lib not in _libcache:
        path = os.path.join(HERE, "fc1.kicad_sym") if lib == "fc1" else SYMDIR + lib + ".kicad_sym"
        t = parse(open(path).read())
        _libcache[lib] = {e[1]: e for e in findall(t, "symbol")}
    return _libcache[lib]


def flat_symbol(lib_id):
    """Return a flattened copy of a library symbol, named lib:name."""
    lib, name = lib_id.split(":")
    syms = load_lib(lib)
    child = syms[name]
    base = child
    ext = find(base, "extends")
    while ext:
        base = syms[ext[1]]
        ext = find(base, "extends")
    out = copy.deepcopy(base)
    out[1] = Q(lib_id)
    if base is not child:
        # child's properties replace the base's; sub-symbols are renamed
        cprops = {p[1]: copy.deepcopy(p) for p in findall(child, "property")}
        props = [cprops.pop(p[1], copy.deepcopy(p)) for p in findall(base, "property")] + list(cprops.values())
        body = [e for e in out if not (isinstance(e, list) and e and e[0] == "property")]
        # insert properties after the header atoms/flags (before first sub-symbol)
        idx = next(i for i, e in enumerate(body) if isinstance(e, list) and e[0] == "symbol")
        out = body[:idx] + props + body[idx:]
        for e in out:
            if isinstance(e, list) and e and e[0] == "symbol":
                e[1] = Q(e[1].replace(base[1], name, 1))
    return out


def pins_of(symdef):
    pins = []
    for sub in findall(symdef, "symbol"):
        for p in findall(sub, "pin"):
            at = find(p, "at")
            pins.append((str(find(p, "number")[1]), float(at[1]), float(at[2]), int(float(at[3])) if len(at) > 3 else 0))
    return pins


def prop(name, value, x, y, hide=False, justify=None, size=1.27):
    eff = ["effects", ["font", ["size", size, size]]]
    if justify:
        eff.append(["justify"] + justify.split())
    if hide:
        eff.append(["hide", "yes"])
    return ["property", Q(name), Q(value), ["at", round(x, 3), round(y, 3), 0], eff]


# ------------------------------------------------------------------ layout
# Schematic positions (mm, A3 sheet, y down), grouped by function.
SCH = {}
def row(refs, x0, y0, dx, dy=0.0):
    for i, r in enumerate(refs):
        SCH[r] = (x0 + i * dx, y0 + i * dy)

row(["J1"], 40.64, 60.96, 0)
row(["U1"], 96.52, 63.5, 0)
row(["C1", "C2", "R1"], 73.66, 35.56, 22.86)
row(["JP1"], 147.32, 35.56, 0)
row(["K1"], 78.74, 101.6, 0)
row(["R2"], 116.84, 99.06, 0)
row(["TP1"], 142.24, 66.04, 0, 12.7)
row(["JP5"], 157.48, 86.36, 0)
row(["Q1"], 45.72, 152.4, 0)
row(["D1", "D2"], 81.28, 139.7, 0, 25.4)
row(["R11", "R12", "R13"], 116.84, 147.32, 15.24)
row(["U2"], 45.72, 205.74, 0)
row(["C5", "C6", "C3", "C4"], 76.2, 203.2, 15.24)
row(["R5", "C10"], 147.32, 203.2, 15.24)
row(["R14"], 182.88, 203.2, 0)
row(["D3"], 205.74, 210.82, 0)
row(["U3"], 246.38, 63.5, 0)
row(["R3", "R4"], 208.28, 53.34, 0, 25.4)
row(["C7", "C8"], 223.52, 101.6, 15.24)
row(["C9", "R10"], 289.56, 101.6, 15.24)
row(["JP2", "JP3", "JP4"], 289.56, 35.56, 0, 17.78)
row(["Q2", "Q3"], 284.48, 170.18, 38.1)
row(["R6", "R7", "R8", "R9"], 205.74, 147.32, 15.24)
row(["C11"], 205.74, 185.42, 0)
row(["J2", "J3"], 337.82, 45.72, 0, 25.4)
row(["J4"], 337.82, 109.22, 0)
row(["H5", "R15"], 248.92, 210.82, 17.78)
row(["H1", "H2", "H3", "H4", "H6"], 289.56, 203.2, 15.24)

FLAGS = {"GND": (391.16, 160.02), "+5V": (391.16, 172.72), "+5VA": (391.16, 185.42), "+3V3": (391.16, 198.12)}

NOTES = [
    (25.4, 20.32, "INPUT AND INTEGRATOR (guarded node SUM: no solder mask, no vias, guard ring on both layers)", 2.0),
    (25.4, 25.4, "Q = -C_f (V_OUT - V_REF).  C_f = 10 nF (JP1 open, about +/-24 nC) or 110 nF (JP1 fitted, about +/-264 nC)", 1.6),
    (25.4, 124.46, "RESET: GP10 high -> Q1 on -> K1 closes across C_f (R2 100R limits the discharge current)", 2.0),
    (25.4, 182.88, "REFERENCE AND POWER: 5 V from the Pico VBUS (J4); +5VA filtered by R5/C4", 2.0),
    (195.58, 20.32, "ADC: ADS1115 at 5 V, AIN0-AIN1 = OUT-REF (differential)", 2.0),
    (195.58, 25.4, "I2C address 0x48 (default, R10); bridge ONE of JP2/JP3/JP4 for 0x49/0x4A/0x4B", 1.6),
    (195.58, 124.46, "I2C LEVEL SHIFT: 3.3 V STEMMA QT bus <-> 5 V ADC (BSS138)", 2.0),
    (325.12, 20.32, "CONNECTORS", 2.0),
    (233.68, 182.88, "CHASSIS / MECHANICAL", 2.0),
    (138.43, 101.6, "JP5: BNC shell to GND (1-2, default) or to GUARD (2-3)", 1.6),
    (25.4, 266.7, "FC-1 Faraday-cup charge amplifier v" + D.VERSION + "  " + D.DATE + "  -  generated by gen_sch.py from fc1_design.py", 1.6),
]

# ------------------------------------------------------------------ build
items = []
lib_ids = []
for ref, (lib_id, *_rest) in D.PARTS.items():
    if lib_id not in lib_ids:
        lib_ids.append(lib_id)
lib_ids.append("power:PWR_FLAG")
libsyms = {lid: flat_symbol(lid) for lid in lib_ids}

wires, labels, ncs, texts, symbols = [], [], [], [], []
STUB = 2.54


def add_label(net, x, y, outward):
    # outward: unit vector from pin to stub end
    ex, ey = x + outward[0] * STUB, y + outward[1] * STUB
    wires.append(["wire", ["pts", ["xy", round(x, 3), round(y, 3)], ["xy", round(ex, 3), round(ey, 3)]],
                  ["stroke", ["width", 0], ["type", "default"]], ["uuid", Q(uid("w", net, x, y))]])
    if outward[0] < 0:
        ang, just = 180, "right bottom"
    elif outward[0] > 0:
        ang, just = 0, "left bottom"
    elif outward[1] < 0:
        ang, just = 90, "left bottom"
    else:
        ang, just = 270, "right bottom"
    labels.append(["label", Q(net), ["at", round(ex, 3), round(ey, 3), ang],
                   ["effects", ["font", ["size", 1.27, 1.27]], ["justify"] + just.split()],
                   ["uuid", Q(uid("l", net, x, y))]])


def place_symbol(ref, lib_id, value, footprint, pinmap, fields, x, y, dnp=False, in_bom=True, power=False):
    sd = libsyms[lib_id]
    s = ["symbol", ["lib_id", Q(lib_id)], ["at", x, y, 0], ["unit", 1],
         ["exclude_from_sim", "no"], ["in_bom", "yes" if in_bom else "no"], ["on_board", "no" if power else "yes"],
         ["dnp", "yes" if dnp else "no"], ["uuid", Q(uid("sym", ref))]]
    pins = pins_of(sd)
    ys = [-py for _, _, py, _ in pins] or [0]
    top = y + min(ys + [-5.08]) - 3.0
    bot = y + max(ys + [5.08]) + 3.0
    if power:
        s += [prop("Reference", ref, x, y + 3.81, hide=True), prop("Value", value, x, y - 3.81)]
    else:
        s += [prop("Reference", ref, x + 3.0, top, justify="left"),
              prop("Value", value, x + 3.0, bot, justify="left"),
              prop("Footprint", footprint, x, y, hide=True),
              prop("Datasheet", "~", x, y, hide=True),
              prop("Description", "", x, y, hide=True)]
        for k, v in fields.items():
            s.append(prop(k, v, x, y, hide=True))
    for num, px, py, ang in pins:
        s.append(["pin", Q(num), ["uuid", Q(uid("pin", ref, num))]])
        X, Y = x + px, y - py
        out = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[ang]
        net = pinmap.get(num, None) if not power else value
        if net is None:
            ncs.append(["no_connect", ["at", round(X, 3), round(Y, 3)], ["uuid", Q(uid("nc", ref, num))]])
        else:
            add_label(net, X, Y, out)
    s.append(["instances", ["project", Q("fc1"), ["path", Q("/" + ROOT_UUID), ["reference", Q(ref)], ["unit", 1]]]])
    symbols.append(s)


for ref, (lib_id, value, fp, pinmap, fields) in D.PARTS.items():
    x, y = SCH[ref]
    place_symbol(ref, lib_id, value, fp, pinmap, fields, x, y, dnp=ref in D.DNP, in_bom=ref not in D.NOT_IN_BOM)

for i, (net, (x, y)) in enumerate(FLAGS.items()):
    place_symbol("#FLG0%d" % (i + 1), "power:PWR_FLAG", net, "", {}, {}, x, y, power=True)

for (x, y, t, size) in NOTES:
    texts.append(["text", Q(t), ["exclude_from_sim", "no"], ["at", x, y, 0],
                  ["effects", ["font", ["size", size, size]], ["justify", "left", "bottom"]],
                  ["uuid", Q(uid("t", t))]])

sch = ["kicad_sch", ["version", 20250114], ["generator", Q("eeschema")], ["generator_version", Q("9.0")],
       ["uuid", Q(ROOT_UUID)], ["paper", Q("A3")],
       ["title_block", ["title", Q("FC-1 Faraday-cup charge amplifier")], ["date", Q(D.DATE)], ["rev", Q(D.VERSION)],
        ["company", Q("vertical-cloud-lab/powder-doser, design/in-house-tests/pcb")],
        ["comment", 1, Q("ADA4530-1 integrator, C_f 10 nF / 110 nF, Coto 9002 reed reset, ADS1115 (0x48) on the accessory Pico I2C")],
        ["comment", 2, Q("Connectivity is by net label. Generated by gen_sch.py; edit fc1_design.py, not this file.")]],
       ["lib_symbols"] + [libsyms[l] for l in lib_ids]]
sch += texts + wires + labels + ncs + symbols
sch += [["sheet_instances", ["path", Q("/"), ["page", Q("1")]]], ["embedded_fonts", "no"]]

with open(os.path.join(HERE, "fc1.kicad_sch"), "w") as f:
    f.write(dumps(sch) + "\n")
print("wrote fc1.kicad_sch with", len(symbols), "symbols,", len(labels), "labels")
