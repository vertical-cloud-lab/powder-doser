"""Lightweight purchased-part stand-ins for the POWDER_DOSER_V2 assembly.

Plain helper module (factories, no models).  Every stand-in is built in the
part's own top-view frame -- board lower-left corner at the origin, module PCB
underside at z = 0 -- and its holes/pins use the coordinates measured from
the vendor STEP models / Eagle boards listed in README.md, so the placements
in pcb_assembly.py register pin-for-pin with the footprints.

Why stand-ins instead of the vendor STEP files: re-emitted by cadgen the
vendor models weigh 5-13 MB each (Tic T500 13.2 MB, Pico W 13.1 MB,
D24V22F5 5.0 MB, shunt 5.1 MB, DRV8871 2.2 MB, KiCad 1x20 header 1.6 MB),
far over the ~5-10 MB budget for committed outputs.  Component envelopes
(caps, terminal blocks, USB, ICs) are taken from the vendor STEP solids where
those are separate bodies, otherwise from the vendor dimension drawings.
"""
from __future__ import annotations

import functools

from cadgen import build123d as bd
from cadgen import srgb

PIN_GOLD = "#D4AF37"
BLACK_PLASTIC = "#1C1C1E"
SILVER = "#C8CCD0"
TB_BLUE = "#2F6DB5"
TB_GREEN = "#2F8F4E"


# ---------------------------------------------------------------- primitives
def box(x0, y0, z0, x1, y1, z1, colour: str, label: str) -> bd.Solid:
    s = bd.Box(x1 - x0, y1 - y0, z1 - z0, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN)).moved(
        bd.Location((x0, y0, z0)))
    s.color = srgb(colour)
    s.label = label
    return s


def cyl(cx, cy, z0, height, dia, colour: str, label: str) -> bd.Solid:
    s = bd.Cylinder(dia / 2, height, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)).moved(
        bd.Location((cx, cy, z0)))
    s.color = srgb(colour)
    s.label = label
    return s


def board(w, h, t, colour, holes=(), label="board") -> bd.Solid:
    """Rectangular PCB (z 0..t) with round holes [(x, y, dia), ...]."""
    b = bd.Box(w, h, t, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
    if holes:
        tools = [bd.Cylinder(d / 2, t + 2, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)).moved(
            bd.Location((x, y, -1))) for x, y, d in holes]
        b = b.cut(bd.Compound(tools))
    b.color = srgb(colour)
    b.label = label
    return b


def group(children, label: str) -> bd.Compound:
    return bd.Compound(children=list(children), label=label)


def row(x0, y0, n, pitch=2.54, dx=0.0, dy=-1.0, dia=1.0):
    return [(x0 + dx * pitch * i, y0 + dy * pitch * i, dia) for i in range(n)]


# ------------------------------------------------------------- 0.1" headers
# Pins are 0.64 mm round posts (3 edges each instead of a square post's 12);
# factories are cached so every placement links one shared definition.
@functools.lru_cache(maxsize=None)
def pin_header(n: int, label: str = "pin_header") -> bd.Compound:
    """Straight male 0.1" header: pin 1 at the origin, pins along -Y,
    plastic z 0..2.54, pins z -3.0..8.54 (KiCad PinHeader convention)."""
    plastic = box(-1.27, -2.54 * (n - 1) - 1.27, 0, 1.27, 1.27, 2.54, BLACK_PLASTIC, "plastic")
    pins = [cyl(0, -2.54 * i, -3.0, 11.54, 0.64, PIN_GOLD, f"pin{i + 1}") for i in range(n)]
    return group([plastic, *pins], label)


@functools.lru_cache(maxsize=None)
def pin_socket(n: int, label: str = "pin_socket") -> bd.Compound:
    """Straight female 0.1" socket: pin 1 at the origin, along -Y, body
    z 0..8.5 (KiCad PinSocket convention), tails z -3.0..0."""
    body = box(-1.27, -2.54 * (n - 1) - 1.27, 0, 1.27, 1.27, 8.5, BLACK_PLASTIC, "body")
    tails = [cyl(0, -2.54 * i, -3.0, 3.0, 0.64, PIN_GOLD, f"tail{i + 1}") for i in range(n)]
    return group([body, *tails], label)


def terminal_block(n: int, pitch: float, depth: float, height: float, colour: str,
                   label: str = "terminal_block") -> bd.Compound:
    """Screw terminal block, wire entries facing -Y.  Origin = pin 1, pins
    along +X; body centred on the pin row in Y."""
    w = n * pitch
    body = bd.Box(w, depth, height, align=(bd.Align.MIN, bd.Align.CENTER, bd.Align.MIN)).moved(
        bd.Location((-pitch / 2, 0, 0)))
    entries = [bd.Box(pitch * 0.6, 2.0, height * 0.45, align=(bd.Align.CENTER, bd.Align.MIN, bd.Align.MIN)).moved(
        bd.Location((pitch * i, -depth / 2 - 0.01, height * 0.15))) for i in range(n)]
    screws = [bd.Cylinder(pitch * 0.32, 1.2, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)).moved(
        bd.Location((pitch * i, 0.6, height - 1.0))) for i in range(n)]
    body = body.cut(bd.Compound(entries + screws))
    body.color = srgb(colour)
    body.label = "body"
    heads = [cyl(pitch * i, 0.6, height - 1.0, 0.8, pitch * 0.6, SILVER, f"screw{i + 1}")
             for i in range(n)]
    return group([body, *heads], label)


# ------------------------------------------------------------------ modules
def pico_w() -> bd.Compound:
    """Raspberry Pi Pico W (21 x 51 x 1.0 mm).  USB at +Y; pin 1 (GP0) at
    (1.61, 49.63).  Component boxes from the step.parts raspberry_pi_pico_w
    solids (shield, RP2040, flash, BOOTSEL, micro-USB)."""
    holes = row(1.61, 49.63, 20) + row(19.39, 49.63, 20)
    holes += [(4.8, 2.0, 2.1), (16.2, 2.0, 2.1), (4.8, 49.0, 2.1), (16.2, 49.0, 2.1)]
    t = 1.0
    parts = [
        board(21.0, 51.0, t, "#2E6B3A", holes, "pcb"),
        box(4.5, 8.2, t, 16.5, 18.2, t + 1.7, SILVER, "cyw43439_shield"),
        box(7.0, 23.55, t, 14.0, 30.55, t + 0.9, "#202020", "rp2040"),
        box(10.77, 38.59, t, 14.77, 41.59, t + 0.8, "#202020", "flash"),
        box(4.2, 19.34, t, 7.4, 21.84, t + 0.9, "#303030", "regulator"),
        box(5.4, 36.87, t, 8.6, 41.12, t + 1.6, "#E8E8E8", "bootsel_body"),
        cyl(7.0, 39.0, t + 1.6, 0.9, 1.6, "#F0F0F0", "bootsel_button"),
        box(15.68, 43.05, t, 17.33, 45.75, t + 0.98, "#F2F2F2", "led"),
        box(6.51, 46.29, t, 14.49, 52.35, t + 2.69, SILVER, "micro_usb"),
    ]
    return group(parts, "raspberry_pi_pico_w")


def waveshare_pico_2ch_rs232() -> bd.Compound:
    """Waveshare Pico-2CH-RS232 (21 x 52 mm, Pico form factor, female Pico
    headers underneath, SP3232EEN, two 3-pin RS-232 connectors).  No vendor
    CAD; envelope per the Waveshare wiki ("21.00 x 52.00 mm")."""
    holes = row(1.61, 50.13, 20) + row(19.39, 50.13, 20)
    holes += [(4.8, 2.0, 2.1), (16.2, 2.0, 2.1), (4.8, 50.0, 2.1), (16.2, 50.0, 2.1)]
    t = 1.6
    parts = [
        board(21.0, 52.0, t, "#1E2A44", holes, "pcb"),
        box(6.5, 22.0, t, 14.5, 32.0, t + 1.6, "#202020", "sp3232een"),
        box(5.0, 36.0, t, 16.0, 40.0, t + 1.2, "#2A2A2A", "tvs_esd"),
        box(4.0, 2.0, t, 10.0, 6.5, t + 6.0, "#EDEDE0", "rs232_ch0_3pin"),
        box(11.0, 2.0, t, 17.0, 6.5, t + 6.0, "#EDEDE0", "rs232_ch1_3pin"),
        box(5.0, 10.0, t, 6.6, 10.8, t + 0.6, "#E04040", "led_txd0"),
        box(14.4, 10.0, t, 16.0, 10.8, t + 0.6, "#40C040", "led_rxd0"),
    ]
    for i, x in enumerate((1.61, 19.39)):
        s = pin_socket(20, f"female_header_{'l' if i == 0 else 'r'}")
        # flipped under the board: body z -8.5..0, tails up through the PCB
        parts.append(bd.Location((x, 50.13, 0), (0, 180, 0)) * s)
    return group(parts, "waveshare_pico_2ch_rs232")


def tic_t500() -> bd.Compound:
    """Pololu Tic T500 (38.1 x 26.67 x 1.57 mm), as fitted to this carrier.
    Holes from the vendor STEP (tic-t500-usb-multi-interface-stepper-motor-
    controller.step); USB, cap and ICs approximated from the Pololu tic03b
    dimension drawing.  The carrier feeds VIN/GND and the motor through the
    Tic's 0.1" row at x = 36.83, which the 6-way 3.5 mm terminal block of the
    pre-soldered #3135 would sit on top of, so the board is modelled bare
    (#3134 style, no terminal block, no factory header)."""
    holes = row(1.27, 25.40, 10) + [(36.83, y, 1.02) for y in (2.54, 5.08, 7.62, 10.16, 15.24, 17.78)]
    holes += row(13.97, 25.40, 5, dx=1.0, dy=0.0)
    holes += [(5.08, 2.54, 2.18), (35.56, 24.13, 2.18)]
    t = 1.57
    holes += [(34.29, 1.75 + 3.5 * i, 1.52) for i in range(6)]   # unused terminal-block holes
    parts = [
        board(38.1, 26.67, t, "#8B1E2B", holes, "pcb"),
        box(3.62, 23.0, t, 11.62, 28.04, t + 2.8, SILVER, "micro_usb"),
        cyl(14.0, 11.5, t, 6.0, 6.3, SILVER, "bulk_cap"),
        box(10.5, 8.0, t, 17.5, 15.0, t + 0.4, BLACK_PLASTIC, "bulk_cap_base"),
        box(21.0, 6.0, t, 25.0, 10.0, t + 0.9, "#202020", "mp6500_driver"),
        box(17.0, 17.5, t, 21.0, 21.5, t + 0.9, "#202020", "mcu"),
        box(23.0, 19.0, t, 29.5, 22.5, t + 1.6, "#202020", "regulator"),
    ]
    return group(parts, "pololu_tic_t500")


def d24v22f5() -> bd.Compound:
    """Pololu D24V22F5 5 V 2.5 A step-down (#2858), 17.78 x 17.78 x 1.02 mm,
    pins PG EN VIN GND VOUT at y = 1.27 (vendor STEP holes); two SMD caps and
    the inductor per the reg19a dimension drawing (6.0 mm tall)."""
    holes = row(1.27, 1.27, 5, dx=1.0, dy=0.0, dia=1.02) + [(1.27, 11.94, 1.02)]
    holes += [(2.29, 15.49, 2.18), (15.49, 2.29, 2.18)]
    t = 1.02
    parts = [board(17.78, 17.78, t, "#2D7A3E", holes, "pcb")]
    for i, cx in enumerate((4.4, 11.0)):
        parts.append(box(cx - 3.3, 7.6 - 3.3, t, cx + 3.3, 7.6 + 3.3, t + 0.6, BLACK_PLASTIC, f"cap{i + 1}_base"))
        parts.append(cyl(cx, 7.6, t + 0.6, 5.4, 6.3, SILVER, f"cap{i + 1}"))
    parts.append(box(11.0, 11.2, t, 17.2, 17.2, t + 4.5, "#3A3A3A", "inductor"))
    parts.append(box(5.5, 5.5, -1.1, 12.0, 12.0, 0.0, "#202020", "bottom_ic"))
    return group(parts, "pololu_d24v22f5")


def shunt_regulator_9w() -> bd.Compound:
    """Pololu 33 V / 9 W shunt regulator (#3776), 28.575 x 20.32 x 1.57 mm.
    Holes and the 12 top-side power resistors from the vendor
    shunt-regulator.step; the bottom-side resistors in that model are only
    fitted on 15 W versions (drawing note 4), so they are omitted."""
    holes = row(4.83, 6.35, 4, dy=1.0, dia=1.02)
    holes += [(2.36, 7.66, 2.18), (2.36, 12.66, 2.18)]
    holes += [(2.16, 2.16, 2.18), (26.42, 2.16, 2.18), (2.16, 18.16, 2.18)]
    holes += [(15.75, 6.10, 1.02), (6.22, 19.05, 1.02)]
    t = 1.57
    parts = [board(28.575, 20.32, t, "#2D7A3E", holes, "pcb")]
    k = 0
    for x0, x1 in ((16.36, 19.71), (20.42, 23.77), (24.49, 27.84)):
        for y0, y1 in ((7.76, 9.51), (10.94, 12.69), (14.11, 15.86), (17.29, 19.04)):
            k += 1
            parts.append(box(x0, y0, t, x1, y1, t + 0.65, "#202020", f"r{k}"))
    parts.append(box(9.45, 11.75, t, 15.75, 18.05, t + 0.5, BLACK_PLASTIC, "cap_base"))
    parts.append(cyl(12.6, 14.9, t + 0.5, 5.6, 6.3, SILVER, "cap"))
    parts.append(box(8.3, 6.0, t, 13.3, 10.6, t + 1.0, "#202020", "mosfet"))
    parts.append(box(5.5, 1.0, t, 8.0, 3.5, t + 0.9, "#202020", "comparator"))
    return group(parts, "pololu_shunt_regulator_9w")


def drv8871() -> bd.Compound:
    """Adafruit DRV8871 breakout (#3190), 20.32 x 24.13 x 1.57 mm.  Header
    JP2 (GND, VM, IN1, IN2 at x = 13.97..6.35, y = 2.54), mounting holes and
    the bodies below from 'Adafruit DRV8871.brd' / '3190 DRV8871 Breakout.step'."""
    holes = row(6.35, 2.54, 4, dx=1.0, dy=0.0)
    holes += [(2.54, 2.54, 2.5), (17.78, 2.54, 2.5)]
    holes += [(4.04, 20.32, 1.0), (7.54, 20.32, 1.0), (12.68, 20.32, 1.0), (16.18, 20.32, 1.0)]
    t = 1.57
    tb = terminal_block(2, 3.5, 7.3, 10.09 - t, TB_BLUE, "tb")
    parts = [
        board(20.32, 24.13, t, "#1F1F24", holes, "pcb"),
        # wire entries face the +Y board edge
        bd.Location((4.04, 20.25, t), (0, 0, 180)) * bd.Location((-3.5, 0, 0)) * tb,
        bd.Location((12.68, 20.25, t), (0, 0, 180)) * bd.Location((-3.5, 0, 0)) * tb,
        box(2.25, 7.89, t, 7.15, 13.92, 3.27, "#202020", "drv8871_hsop8"),
        box(10.8, 7.89, t, 18.15, 14.46, t + 0.5, BLACK_PLASTIC, "cap_base"),
        cyl(14.47, 11.17, t + 0.5, 5.1, 6.3, SILVER, "bulk_cap"),
        box(12.08, 5.72, t, 14.08, 6.98, 2.42, "#202020", "r_ilim"),
    ]
    return group(parts, "adafruit_drv8871")


def drv2605l_stemma() -> bd.Compound:
    """Adafruit DRV2605L haptic driver, STEMMA QT revision (#2305), 25.4 x
    17.78 x 1.6 mm.  From 'Adafruit DRV2605L STEMMA QT.brd': header JP2
    (VCC GND SCL SDA IN at x = 7.62..17.78, y = 2.54), four 2.5 mm holes,
    two JST-SH 4-pin connectors at the short edges, OUT+/- pads."""
    holes = row(7.62, 2.54, 5, dx=1.0, dy=0.0)
    holes += [(2.54, 2.54, 2.5), (22.86, 2.54, 2.5), (2.54, 15.24, 2.5), (22.86, 15.24, 2.5)]
    holes += [(17.78, 15.24, 1.0), (7.62, 15.24, 1.0)]
    t = 1.6
    parts = [
        board(25.4, 17.78, t, "#1F1F24", holes, "pcb"),
        box(20.6, 5.9, t, 24.85, 11.9, t + 2.95, "#EDEDE0", "stemma_qt_right"),
        box(0.55, 5.9, t, 4.8, 11.9, t + 2.95, "#EDEDE0", "stemma_qt_left"),
        box(11.2, 8.0, t, 14.2, 11.0, t + 1.0, "#202020", "drv2605l"),
        box(15.5, 8.4, t, 17.0, 9.2, t + 0.6, "#202020", "c1"),
    ]
    return group(parts, "adafruit_drv2605l_stemma_qt")


def wood_screw_10(length: float = 25.4) -> bd.Solid:
    """#10 flat-head (82 deg) wood screw stand-in: 4.83 mm shank, 9.7 mm head,
    tapered point.  Head top at z = 0, shank along -Z.  (No wood screws in
    the step.parts catalog.)"""
    import math
    r_sh, r_hd = 4.83 / 2, 9.7 / 2
    h_hd = (r_hd - r_sh) / math.tan(math.radians(41))
    pts = [(0, 0), (r_hd, 0), (r_sh, -h_hd), (r_sh, -(length - 4.0)), (0.4, -length), (0, -length)]
    prof = bd.Polyline(*pts, close=True)
    s = bd.revolve(bd.make_face(bd.Plane.XZ * prof), bd.Axis.Z)
    slot = bd.Box(1.2, 6.0, 1.2, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX))
    slot2 = bd.Box(6.0, 1.2, 1.2, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX))
    s = s.cut(slot, slot2)
    s.color = srgb("#B8B8B0")
    s.label = "wood_screw_10x1in"
    return s
