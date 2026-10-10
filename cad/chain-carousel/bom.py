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
ITEMS = [
    # ---- chain & sprockets
    (1, ("chain_inner", "chain_outer"), None, "ANSI #35 roller chain, 3 ft (96 pitches) + 2 connecting links",
     "Amazon (Aobbmok)", "B0C1YTF613", "https://www.amazon.com/Aobbmok-Roller-Chain-Connecting-Replacements/dp/B0C1YTF613/",
     7.99, "1 box (on the ME order)", (8,), "Chain"),
    (2, ("chain_a1",), None, "#35 A-1 attachment connecting link (bent tab, 1 hole), replaces 12 riveted outer links",
     "Red Boar Chain", "35 A1 C/L", "https://redboarchain.com/products/35-a1-c-l-attachment-connecting-link-for-35-roller-chain",
     21.75, "each", (8,), "Chain"),
    (3, None, 1, "#35 chain breaker / pin press (removes the 11 outer links the A-1 links replace)",
     "Amazon", "", "https://www.amazon.com/s?k=%2335+roller+chain+breaker", 15.0, "tool", (8,), "Tools"),
    (4, ("sprocket_drive",), None, "Sprocket 35B19, 19T ANSI 35, B hub, bored 14 mm H7 + 5 mm keyway (NEMA 34 shaft)",
     "USA Roller Chain", "35B19", "https://usarollerchain.com/products/35b19-sprocket", 14.99,
     "stock bore; bore + keyway in the BYU shop", (6,), "Chain"),
    (5, ("sprocket_idler",), None, "Idler sprocket #35 19T with ball bearing, 1/2 in bore",
     "Amazon", "B07LDKCN1X", "https://www.amazon.com/HEAVY-ROLLER-CHAIN-SPROCKET-IDLER/dp/B07LDKCN1X", 7.99, "each", (5,), "Chain"),
    # ---- drive
    (6, ("nema34",), None, "NEMA 34 closed-loop stepper 34HS59-6004D-E1000, 12 N*m, 14 mm keyed shaft",
     "StepperOnline", "34HS59-6004D-E1000",
     "https://www.omc-stepperonline.com/s-series-nema-34-closed-loop-stepper-motor-12-0-nm-1699-68oz-in-encoder-1000ppr-4000cpr-34hs59-6004d-e1000",
     0.0, "already bought by UofU", (3,), "Drive"),
    (7, ("key_5x5",), None, "Key 5 x 5 x 25 mm (ships with the motor)", "StepperOnline", "", "", 0.0, "with motor", (6,), "Drive"),
    (8, ("motor_plate",), None, "Motor plate, 6061 aluminium 1/4 in x 6 in x 6 in, cut to 140 x 140 and drilled (DXF in dxf/)",
     "McMaster-Carr", "89015K251", "https://www.mcmaster.com/89015K251/", 22.0, "1 piece", (3,), "Drive"),
    (9, ("cl86t",), None, "Closed-loop stepper driver CL86T V4.1 (24-80 VDC)", "StepperOnline", "CL86T",
     "https://www.omc-stepperonline.com/closed-loop-stepper-driver-0-8-2a-18-80vac-24-110vdc-for-nema-34-stepper-motor-cl86t",
     47.43, "each", (12,), "Drive"),
    (10, ("lrs350",), None, "Power supply Mean Well LRS-350-36 (36 V, 9.7 A)", "Digi-Key", "LRS-350-36",
     "https://www.digikey.com/en/products/detail/mean-well-usa-inc/LRS-350-36/7705124", 40.0, "each", (12,), "Drive"),
    # ---- frame & deck
    (11, ("ext_long",), None, "2020 T-slot extrusion, 1050 mm (long rails)", "Misumi", "HFS5-2020-1050",
     "https://us.misumi-ec.com/vona2/detail/110302683830/", 13.0, "cut to length", (1,), "Frame"),
    (12, ("ext_cross",), None, "2020 T-slot extrusion, 690 mm (cross members)", "Misumi", "HFS5-2020-690",
     "https://us.misumi-ec.com/vona2/detail/110302683830/", 9.0, "cut to length", (1,), "Frame"),
    (13, ("ext_leg",), None, "2020 T-slot extrusion, 230 mm (legs)", "Misumi", "HFS5-2020-230",
     "https://us.misumi-ec.com/vona2/detail/110302683830/", 4.0, "cut to length", (2,), "Frame"),
    (14, ("corner_bracket",), None, "2020 corner bracket with M5 screws and T-nuts", "Amazon", "",
     "https://www.amazon.com/s?k=2020+corner+bracket+m5", 0.60, "20-pack ~$12", (1,), "Frame"),
    (15, ("foot",), None, "Leveling foot M8 (with M8 tapped end in the extrusion bore, or T-nut adapter)", "Amazon", "",
     "https://www.amazon.com/s?k=leveling+feet+m8", 2.0, "4-pack ~$8", (2,), "Frame"),
    (16, ("deck",), None, "Deck, HDPE 1/2 in, 48 x 48 in sheet cut to 1050 x 740 (DXF in dxf/)", "McMaster-Carr", "8619K478",
     "https://www.mcmaster.com/8619K478/", 165.0, "1 sheet", (4,), "Frame"),
    # ---- idler hardware
    (17, ("idler_stud",), None, "Hex bolt 1/2-13 x 2-1/2 in (idler stud)", "McMaster-Carr", "92620A724",
     "https://www.mcmaster.com/92620A724/", 1.5, "each", (5,), "Fasteners"),
    (18, ("nut_38",), None, "Nylon-insert locknut 1/2-13", "McMaster-Carr", "95615A140", "https://www.mcmaster.com/95615A140/",
     0.5, "each", (5,), "Fasteners"),
    (19, ("washer_38",), None, "Washer 1/2 in", "McMaster-Carr", "98023A033", "https://www.mcmaster.com/98023A033/", 0.2,
     "each", (5,), "Fasteners"),
    # ---- fasteners
    (20, ("m5x18_shcs",), None, "M5 x 18 socket head screw (motor flange into the M5-tapped plate)", "McMaster-Carr", "91292A126",
     "https://www.mcmaster.com/91292A126/", 0.25, "pack of 50", (3,), "Fasteners"),
    (21, ("m5x20_fhcs",), None, "M5 x 20 flat head screw + nut (motor plate up into the deck)", "McMaster-Carr", "92125A212",
     "https://www.mcmaster.com/92125A212/", 0.30, "pack of 25", (4,), "Fasteners"),
    (22, ("m5x25_fhcs",), None, "M5 x 25 flat head screw (deck to frame)", "McMaster-Carr", "92125A214",
     "https://www.mcmaster.com/92125A214/", 0.30, "pack of 25", (4,), "Fasteners"),
    (23, ("tnut_m5",), None, "M5 drop-in T-nut, 2020 slot 6", "Amazon", "", "https://www.amazon.com/s?k=2020+drop+in+t+nut+m5", 0.10,
     "100-pack ~$10", (4,), "Fasteners"),
    (24, ("m5x40_shcs",), None, "M5 x 40 socket head screw + nut (tensioner jack screw)", "McMaster-Carr", "91292A135",
     "https://www.mcmaster.com/91292A135/", 0.4, "each", (5,), "Fasteners"),
    (25, ("m3x10_bhcs",), None, "M3 x 10 button head screw (carriage to A-1 tab)", "McMaster-Carr", "92095A181",
     "https://www.mcmaster.com/92095A181/", 0.12, "pack of 100", (9,), "Fasteners"),
    (26, ("insert_m3",), None, "M3 heat-set insert, 5.7 mm long", "McMaster-Carr", "94180A333", "https://www.mcmaster.com/94180A333/",
     0.20, "pack of 100", (9,), "Fasteners"),
    (27, ("m4x30_shcs",), None, "M4 x 30 socket head screw + nylon locknut (hold-down blocks)", "McMaster-Carr", "91292A120",
     "https://www.mcmaster.com/91292A120/", 0.25, "pack of 50", (10,), "Fasteners"),
    (28, ("m5x70_shcs",), None, "M5 x 70 socket head screw + nylon locknut (hinge pin)", "McMaster-Carr", "91292A139",
     "https://www.mcmaster.com/91292A139/", 0.6, "each", (11,), "Fasteners"),
    # ---- printed parts
    (29, ("carriage",), None, "Carriage base plate, printed PETG (H2D bed; ~125 g each)", "printed", "carriage.stl", "", 2.5,
     "filament", (9,), "Printed"),
    (30, ("idler_slider", "tensioner_block", "idler_spacer"), None,
     "Idler slider, spacer and tensioner block, printed PETG", "printed", "idler_*.stl", "", 0.5, "filament", (5,), "Printed"),
    (31, ("hold_down",), None, "Hold-down block, printed PETG", "printed", "hold_down.stl", "", 0.3, "filament", (10,), "Printed"),
    (32, ("hall_holder",), None, "Hall sensor holder, printed PETG", "printed", "hall_holder.stl", "", 0.05, "filament", (7,),
     "Printed"),
    # ---- sensing & electronics
    (33, ("a3144",), None, "A3144 hall-effect switch (open collector), index + home", "Amazon", "",
     "https://www.amazon.com/s?k=a3144+hall+effect+sensor", 0.5, "10-pack ~$6", (7,), "Electronics"),
    (34, ("magnet",), None, "Neodymium disc magnet 6 x 3 mm N52 (12 index + 1 home)", "Amazon", "",
     "https://www.amazon.com/s?k=6x3mm+n52+magnets", 0.15, "50-pack ~$8", (9,), "Electronics"),
    (35, ("raspberry_pi",), None, "Raspberry Pi 4 Model B (any Pi with pigpio works; the lab's spare)", "Adafruit", "4296",
     "https://www.adafruit.com/product/4296", 35.0, "each", (12,), "Electronics"),
    (36, ("perfboard",), None, "Interface board: ULN2803A (step/dir/enable to the CL86T opto inputs), 3 x 10k pull-ups to 3.3 V, screw terminals, perfboard",
     "Digi-Key", "ULN2803A", "https://www.digikey.com/en/products/detail/texas-instruments/ULN2803ADWR/277680", 4.0, "kit", (12,),
     "Electronics"),
    (37, ("estop",), None, "E-stop mushroom switch, NC, in enclosure (breaks the 36 V DC feed to the driver)", "Amazon", "",
     "https://www.amazon.com/s?k=emergency+stop+switch+enclosure", 15.0, "each", (12,), "Electronics"),
    (38, ("board_panel",), None, "Electronics board, 1/4 in plywood 420 x 300", "Home Depot", "", "", 6.0, "offcut", (12,),
     "Electronics"),
    (39, None, 1, "Wire, fuses and connectors: 18 AWG (36 V), 22 AWG (signals), IEC C14 inlet with fuse + switch, 4-pin motor + encoder extension",
     "Amazon", "", "", 25.0, "lot", (12,), "Electronics"),
    # ---- module 1 (exists already in the lab)
    (40, ("sam_mounting_plate",), None, "Mounting plate (Sam's Oct 8 Onshape design), printed", "lab", "Onshape 581956d5",
     "https://cad.onshape.com/documents/581956d5528927957a4c0b98/w/5778b22212c6736ada520515/e/24d73974055f92c0f2fa292f",
     0.0, "existing", (11,), "Module"),
    (41, ("auger", "auger_cap"), None, "Auger, threaded storage, and cap (lab design, PR #170)", "lab", "auger.step", "", 0.0,
     "existing", (11,), "Module"),
    # ---- test equipment (not in CAD)
    (42, None, 1, "Digital dial indicator 0-12.7 mm x 0.01 mm with magnetic base (lift and sag tests)", "Amazon", "",
     "https://www.amazon.com/s?k=digital+dial+indicator+magnetic+base", 30.0, "each", (13,), "Test"),
    (43, None, 1, "Push-pull force gauge 50 N (station push-up, drag force)", "Amazon", "",
     "https://www.amazon.com/s?k=digital+force+gauge+50n", 40.0, "each", (13,), "Test"),
    (44, None, 1, "ADXL345 accelerometer breakout (carriage vibration in transit)", "Adafruit", "4097",
     "https://www.adafruit.com/product/4097", 8.0, "each", (13,), "Test"),
    (45, None, 11, "Dummy module mass: 250 g bag of table salt (or 2 x 125 g steel bars) per carriage", "grocery", "", "", 1.0,
     "each", (13,), "Test"),
]


def counted() -> Counter:
    import layout
    return Counter(p.key for p in layout.placements())


def rows() -> list[dict]:
    n = counted()
    out = []
    for item, keys, qty, desc, vendor, pn, url, price, pack, steps, cat in ITEMS:
        q = sum(n[k] for k in keys) if keys else qty
        if item == 1:
            q = 1                                   # the chain is one box; 84 links of it are in the CAD
        if item == 21:
            q = n["m5x20_fhcs"]
        out.append(dict(item=item, qty=q, description=desc, vendor=vendor, part_number=pn, url=url,
                        unit_usd=price, ext_usd=round(q * price, 2), pack=pack,
                        steps=",".join(map(str, steps)), category=cat, keys=",".join(keys or ())))
    return out


def step_lines() -> dict[int, list[str]]:
    """Per assembly step, the BoM lines it uses (for the step renders)."""
    out: dict[int, list[str]] = {}
    for r in rows():
        for s in map(int, r["steps"].split(",")):
            out.setdefault(s, []).append(f"[{r['item']}] {r['qty']} x {r['description'][:70]}")
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
