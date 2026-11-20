"""Bill of materials for the chain-carousel test rig.

ITEMS is the single table: item number, what, where to buy it, price, and
which assembly step uses it. Quantities of modelled parts are counted from
layout.placements(), so the BoM and the CAD cannot drift apart; unmodelled
items (wire, tools, test gear) carry their own quantity.

    python bom.py        # writes BOM.md and bom.csv
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (item, keys counted from the CAD or None, qty if not counted, description,
#  vendor, part number, url, unit price USD, pack note, steps, category)
V = "verified 2026-10-10"
E = "estimate, not verified"

ITEMS = [
    # ---- chain & sprockets
    (1, None, 1, "ANSI #35 roller chain, 3 ft (96 pitches) + 2 connecting links (now listed as AZSSMUK)",
     "Amazon", "B0C1YTF613", "https://www.amazon.com/dp/B0C1YTF613", 7.99, f"on the ME order; {V} via the Pi", (8,), "Chain"),
    (2, ("chain_a1",), None, "#35 A-1 attachment connecting link (bent tab, 0.10 in hole, M2.5); buy a 10-pack + a 5-pack",
     "Red Boar Chain", "35 A1 C/L", "https://redboarchain.com/products/35-a1-c-l-attachment-connecting-link-for-35-roller-chain",
     60.67 / 15, f"10-pack $38.92 + 5-pack $21.75; {V}", (8,), "Chain"),
    (3, None, 1, "Chain breaker CB25/60 (#25-#60)", "Red Boar Chain", "CB25/60",
     "https://redboarchain.com/products/cb25-60-roller-chain-breaker-breaks-25-thru-60-chain", 22.53, V, (8,), "Tools"),
    (4, ("sprocket_drive",), None, "Sprocket 35B19, 19T ANSI 35, B hub, stock bore; shop bores it to 14 mm H7 + 5 mm keyway",
     "USA Roller Chain", "35B19", "https://usarollerchain.com/products/35b19-sprocket", 15.99,
     f"{V}; $300 web minimum, order by phone (407-347-3519)", (6,), "Chain"),
    (5, ("sprocket_idler",), None, "Idler sprocket #35 19T with ball bearing, 1/2 in bore",
     "Amazon", "B07LDKCN1X", "https://www.amazon.com/dp/B07LDKCN1X", 7.99, f"{V} via the Pi", (5,), "Chain"),
    # ---- drive
    (6, ("nema34",), None, "NEMA 34 closed-loop stepper 34HS59-6004D-E1000, 12 N*m, 6 A, 14 mm x 37 mm keyed shaft",
     "StepperOnline", "34HS59-6004D-E1000",
     "https://www.omc-stepperonline.com/s-series-nema-34-closed-loop-stepper-motor-12-0-nm-1699-68oz-in-encoder-1000ppr-4000cpr-34hs59-6004d-e1000",
     0.0, "already bought by UofU", (3,), "Drive"),
    (7, None, 1, "Key 5 x 5 x 25 mm (ships in the motor's keyway)", "StepperOnline", "", "", 0.0, "with the motor", (6,), "Drive"),
    (8, ("motor_plate",), None, "Motor plate, 6061 aluminium 1/4 in, 140 x 140, from dxf/motor_plate.dxf (pilot bore, 4 x M5 tapped)",
     "local metal supplier / BYU shop stock", "", "", 20.0, E, (3,), "Drive"),
    (9, ("cl86t",), None, "Closed-loop stepper driver CL86T V4.1 (24-80 VDC, 5 V/24 V logic selector)", "StepperOnline (OzRobotics)",
     "CL86T", "https://ozrobotics.com/shop/closed-loop-stepper-driver-v4-1-08-2a-2480vdc-for-nema-34-stepper-motor/", 47.43, V,
     (12,), "Drive"),
    (10, ("lrs350",), None, "Power supply Mean Well LRS-350-48 (48 V, 7.3 A)", "TRC Electronics", "LRS-350-48",
     "https://www.trcelectronics.com/products/mean-well-lrs-350-48", 36.11, V, (12,), "Drive"),
    # ---- frame & deck
    (11, None, 1,
     "2020 T-slot extrusion, 10 x 1000 mm pack: 2 bars whole (rails), 7 cut to 690 (cross members), 4 legs of 230 from the offcuts",
     "VEVOR", "10 x 1000 mm",
     "https://www.vevor.com/linear-guide-rail-c_10531/10pcs-39-4in-1000mm-t-slot-2020-aluminum-extrusion-anodized-linear-rail-p_010731760492",
     66.90, V, (1, 2), "Frame"),
    (12, ("corner_bracket",), None, "2020 90-degree corner bracket", "West3D", "NA03",
     "https://west3d.com/products/angle-corner-connector-90-degree-like-openbuilds", 1.59, V, (1, 2), "Frame"),
    (13, None, 56, "M5 x 10 button head screw for the brackets (2 per bracket)", "West3D", "LDO3385M5X",
     "https://west3d.com/products/ldo-black-screws-nuts-and-various-fasteners-black", 1.99 / 50, f"50-pack $1.99; {V}", (1, 2),
     "Frame"),
    (14, ("tnut_m5",), 56, "M5 drop-in T-nut, 2020 slot 6 (brackets + deck screws)", "West3D", "",
     "https://west3d.com/products/roll-in-drop-in-t-nuts-for-2020-extrusions-m3-3mm-and-m5-5mm-threads", 0.17, V, (1, 4),
     "Frame"),
    (15, ("foot",), None, "Leveling foot, M5 stud (into the leg's centre bore, tapped M5)", "Amazon", "",
     "https://www.amazon.com/s?k=m5+leveling+feet+2020+extrusion", 2.0, E, (2,), "Frame"),
    (16, ("deck_left", "deck_right"), None, "HDPE sheet 1/2 x 24 x 48 in, white; one per deck half (455 and 595 x 740 mm)", "VEVOR",
     "", "https://www.vevor.com/hdpe-sheets-c_13698/1-pack-hdpe-plastic-sheet-board-24-x-48-inch-plastic-panel-1-2-inch-",
     74.90, V, (4,), "Frame"),
    # ---- idler hardware
    (17, ("idler_stud",), None, "Idler stud: 1/2-13 x 2-1/2 in hex bolt, Grade 5, with a 1/2-13 nylock nut and a washer",
     "BoltsAndNuts.com", "", "https://boltsandnuts.com/products/1-2-13x2-1-2-hex-cap-screws-grade-5-bolts-zinc-clear", 2.55,
     f"set $2.55; {V}", (5,), "Fasteners"),
    # ---- fasteners
    (20, None, 4, "M5 x 12 socket head screw (motor flange into the M5-tapped plate)", "BoltsAndNuts.com", "",
     "https://boltsandnuts.com/products/m5-0-8x12-class-12-9-alloy-socket-head-cap-screws-black-oxide", 12.21 / 100,
     f"100-pack $12.21; {V}", (3,), "Fasteners"),
    (21, ("m5x18_fhcs",), None, "M5 x 18 flat head (countersunk) screw, deck to frame T-nuts", "BoltsAndNuts.com / McMaster", "",
     "", 0.15, E, (4,), "Fasteners"),
    (22, ("m5x25_fhcs",), None, "M5 x 25 flat head screw (motor plate and slider clamps, through the deck)",
     "BoltsAndNuts.com / McMaster", "", "", 0.20, E, (4, 5), "Fasteners"),
    (18, ("nut_m5",), None, "M5 nylock nut (motor plate, slider clamps, jack screw)", "BoltsAndNuts.com / McMaster", "", "", 0.06,
     E, (4, 5), "Fasteners"),
    (23, ("m5x40_shcs",), None, "M5 x 40 socket head screw (tensioner jack screw)", "BoltsAndNuts.com / McMaster", "", "", 0.30,
     E, (5,), "Fasteners"),
    (24, ("m4x20_fhcs",), None, "M4 x 20 flat head screw (tensioner block, down from the deck into the PETG)",
     "BoltsAndNuts.com / McMaster", "", "", 0.15, E, (5,), "Fasteners"),
    (25, ("m25x8_bhcs",), None, "M2.5 x 8 button head screw (carriage to A-1 tab, through the 0.10 in hole)",
     "BoltsAndNuts.com / McMaster", "", "", 0.12, E, (9,), "Fasteners"),
    (26, ("insert_m25",), None, "M2.5 heat-set insert (CNC Kitchen), in each carriage's inner wall", "West3D", "",
     "https://west3d.com/products/cnc-kitchen-heat-set-inserts-various-sizes", 0.15, E, (9,), "Fasteners"),
    (27, ("m4x25_shcs",), None, "M4 x 25 socket head screw, each into an M4 drop-in T-nut in the front rail (hold-downs)",
     "West3D / BoltsAndNuts.com", "", "", 0.30, E, (10,), "Fasteners"),
    (28, None, 2, "M5 x 18 socket head screw + nylock nut (module 1 hinge pins, one per side)", "BoltsAndNuts.com / McMaster",
     "", "", 0.25, E, (11,), "Fasteners"),
    # ---- printed parts
    (29, ("carriage",), None, "Carriage, PETG (H2D bed; about 125 g each)", "printed", "stl/carriage.stl", "", 2.5,
     "filament at $20/kg", (9,), "Printed"),
    (30, ("idler_slider", "tensioner_block", "idler_spacer"), None,
     "Idler slider, spacer and tensioner block, PETG (print the spacer to suit the idler's measured width)", "printed",
     "stl/idler_*.stl, stl/tensioner_block.stl", "", 0.5, "filament", (5,), "Printed"),
    (31, ("hold_down",), None, "Hold-down block, PETG", "printed", "stl/hold_down.stl", "", 0.3, "filament", (10,), "Printed"),
    (32, ("hall_holder",), None, "Hall sensor holder, PETG", "printed", "stl/hall_holder.stl", "", 0.05, "filament", (7,),
     "Printed"),
    # ---- sensing & electronics
    (33, ("a3144",), None, "Hall-effect switch US5881 (unipolar, open drain, TO-92): INDEX and HOME", "Adafruit", "158",
     "https://www.adafruit.com/product/158", 2.00, V, (7,), "Electronics"),
    (34, ("magnet",), None, "Neodymium disc magnet D42-N52, 1/4 x 1/8 in (12 index + 1 home)", "K&J Magnetics", "D42-N52",
     "https://www.kjmagnetics.com/d42-n52-neodymium-disc-magnet", 0.52, V, (9,), "Electronics"),
    (35, ("raspberry_pi",), None, "Raspberry Pi Zero 2 W (or any spare Pi that runs pigpio)", "Adafruit", "5291",
     "https://www.adafruit.com/product/5291", 15.00, E, (12,), "Electronics"),
    (36, ("perfboard",), None, "Interface board: 74AHCT125 (3.3 V GPIO to 5 V step/dir/enable), 3 x 10k pull-ups to 3.3 V, screw terminals, perfboard",
     "Adafruit", "1787", "https://www.adafruit.com/product/1787", 6.0, E, (12,), "Electronics"),
    (37, ("estop",), None, "E-stop GCX1136 (22 mm, NC, twist to release) + enclosure; breaks the 48 V feed to the driver",
     "AutomationDirect", "GCX1136", "https://www.automationdirect.com/pn/GCX1136", 30.0, f"$21 + $9 box; {V}", (12,),
     "Electronics"),
    (38, ("board_panel",), None, "Electronics board, 1/4 in plywood 420 x 300", "Home Depot", "", "", 6.0, E, (12,), "Electronics"),
    (39, None, 1, "IEC C14 inlet with switch + fuse drawer (Qualtek 719W-UEL3BR51)", "Digi-Key", "719W-UEL3BR51",
     "https://www.digikey.com/en/products/detail/qualtek/719W-UEL3BR51/23019206", 7.66, V, (12,), "Electronics"),
    (40, None, 1, "18 AWG stranded hook-up wire, 25 ft (48 V and motor)", "Digi-Key", "18UL1007STRBLA25",
     "https://www.digikey.com/en/products/result?keywords=18UL1007STRBLA25", 14.57, V, (12,), "Electronics"),
    # ---- module 1 (exists already in the lab)
    (41, ("sam_mounting_plate",), None, "Mounting plate (Sam's Oct 8 Onshape design), printed", "lab", "Onshape 581956d5",
     "https://cad.onshape.com/documents/581956d5528927957a4c0b98/w/5778b22212c6736ada520515/e/24d73974055f92c0f2fa292f",
     0.0, "existing", (11,), "Module"),
    (42, ("auger", "auger_cap"), None, "Auger, threaded storage, and cap (lab design, PR #170)", "lab", "reference/auger-*.step", "",
     0.0, "existing", (11,), "Module"),
    # ---- test equipment (not in CAD)
    (43, None, 1, "Digital indicator 0-1 in / 0.01 mm with arm and magnetic base (lift, sag, index tests)", "Penn Tool Co",
     "iGaging 35-520", "https://www.penntoolco.com/igaging-digital-indicator-universal-arm-magnetic-base-set-35-520", 119.95, V,
     (13,), "Test"),
    (44, None, 1, "Digital hanging scale 50 kg (drag and push-up force; a 50 N push-pull gauge is better if the lab has one)",
     "Etekcity", "EL11", "https://etekcity.com/products/luggage-scale-el11", 10.99, V, (13,), "Test"),
    (45, None, 1, "ADXL343 accelerometer breakout (transit vibration)", "Adafruit", "4097", "https://www.adafruit.com/product/4097",
     5.95, V, (13,), "Test"),
    (46, None, 11, "Dummy module mass: 250 g bag of table salt per carriage", "grocery", "", "", 0.5, E, (13,), "Test"),
]


# lines you can only buy in packs larger than the rig uses: what you actually pay
BUY = {2: 60.67}

NOTES = """**Before ordering sprockets, measure the chain that arrived.** The Amazon listing no longer gives dimensions.
ANSI #35 has a 0.200 in (5.08 mm) bushing and 0.188 in (4.78 mm) between the inner plates. ISO 06B has the same
3/8 in pitch but a 6.35 mm roller and 5.72 mm between the plates, and the two don't mix: a 5.3 mm 06B tooth can't
enter a #35 chain, and a 0.168 in #35 tooth rattles in 06B. (ISO 06C *is* ANSI 35.)

**Attachment-link holes are 0.10 in (M2.5).** McMaster's 7321K1 (A-1) and 7321K31 (SA-1) have a 0.134 in hole
for M3, but their prices don't show without a login. Drilling the Red Boar tabs to 3.2 mm leaves about 2.35 mm
of metal each side, which is plenty for this load.

**USA Roller Chain has a $300 web minimum.** Order the 35B19 by phone, or take Red Boar's 35B19H ($16.95, pick
the bore, out of stock on 2026-10-10). No vendor checked lists a 19T #35 sprocket with a 14 mm bore and 5 mm
keyway, so the plan is a stock-bore blank bored in the BYU shop.

**Prices** are as listed on 2026-10-10 by vendor (`verified`), or estimates for generic hardware (`estimate`).
The two `Amazon` prices were read through the powder-doser Pi, because Amazon blocks the CI runner's IP."""


def counted() -> Counter:
    import layout
    return Counter(p.key for p in layout.placements())


def rows() -> list[dict]:
    n = counted()
    out = []
    for item, keys, qty, desc, vendor, pn, url, price, pack, steps, cat in ITEMS:
        q = sum(n[k] for k in keys) if keys else qty
        if item == 14:
            q = n["tnut_m5"] + 2 * n["corner_bracket"]
        if item == 13:
            q = 2 * n["corner_bracket"]
        ext = BUY.get(item, q * price)
        out.append(dict(item=item, qty=q, description=desc, vendor=vendor, part_number=pn, url=url,
                        unit_usd=round(price, 2), ext_usd=round(ext, 2), pack=pack,
                        steps=",".join(map(str, steps)), category=cat, keys=",".join(keys or ())))
    return out


def step_lines() -> dict[int, list[str]]:
    """Per assembly step, the BoM lines it uses (for the step renders)."""
    out: dict[int, list[str]] = {}
    for r in rows():
        for s in map(int, r["steps"].split(",")):
            d = r["description"]
            out.setdefault(s, []).append(f"[{r['item']}] {r['qty']} x {d if len(d) <= 100 else d[:97] + '...'}")
    return out


def write() -> None:
    rs = rows()
    with (HERE / "bom.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rs[0]))
        w.writeheader()
        w.writerows(rs)
    total = sum(r["ext_usd"] for r in rs)
    buy = sum(r["ext_usd"] for r in rs if r["category"] not in ("Test",))
    print(f"{len(rs)} lines, total ${total:.2f} (rig without test gear ${buy:.2f})")


if __name__ == "__main__":
    write()
