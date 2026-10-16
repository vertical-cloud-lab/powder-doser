"""Bill of materials for the chain-carousel test rig v2 (vertical twin chain).

ITEMS is the single table: item number, what, where to buy it, price, and
which assembly step uses it. Quantities of modelled parts are counted from
layout.placements(), so the BoM and the CAD cannot drift apart; unmodelled
items (wire, tools, test gear) carry their own quantity.

    python bom.py        # writes bom.csv
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (item, keys counted from the CAD or None, qty if not counted, description,
#  vendor, part number, url, unit price USD, pack note, steps, category)
V = "verified 2026-10-13"
V10 = "verified 2026-10-10 (v1 BoM)"
E = "estimate, not verified"
SC = "https://www.surpluscenter.com"
NITRO_A1 = "https://www.nitrochain.com/35-a1-standard-attachment-connecting-link"

ITEMS = [
    # ---- chain & sprockets
    (1, None, 1, "ANSI #35 roller chain, 10 ft roll (320 pitches, 1 connecting link): two 104-link loops + the 44-link drive chain",
     "Nitro Chain", "RC35-1R-10FT", "https://www.nitrochain.com/35-roller-chain-10ft", 23.53, V, (6, 7), "Chain"),
    (2, ("chain_a1",), None, "#35 A-1 attachment connecting link, spring clip, 0.133 in hole (M3): 13 per chain",
     "Nitro Chain", "CL35-A1", NITRO_A1, 2.55, V, (7,), "Chain"),
    (3, None, 1, "Roller chain breaker, #25-#60 (Dura-Roll #1)", "Surplus Center", "100115",
     "https://surpluscenter.com/1-roller-chain-breaker-for-25-60-pitch/", 17.20, V, (6, 7), "Tools"),
    (4, ("sprocket_32",), None, "Sprocket 35BS32-5/8: 32T, type B, 2 in hub, 7/8 in through the bore, 5/8 in bore, 3/16 in keyway, 2 set screws",
     "Surplus Center", "601139", f"{SC}/32t-5-8-bore-35p-sprocket/", 21.55, V, (5,), "Chain"),
    (5, ("sprocket_15_shaft",), None, "Sprocket 35BS15H-5/8: 15T, 5/8 in bore, 3/16 in keyway (drive chain, on the B+ shaft's stub)",
     "Surplus Center", "601078", f"{SC}/15t-5-8-bore-35p-sprocket/", 6.65, V, (6,), "Chain"),
    (6, ("sprocket_15_motor",), None, "Sprocket 35BS15H-1/2: 15T, 1/2 in bore; shop re-bores it to 14 mm H7 with a 5 mm keyway for the NEMA 34",
     "Surplus Center", "601077", f"{SC}/15t-1-2-bore-35p-sprocket/", 6.65, V, (6,), "Chain"),
    # ---- shafts & bearings
    (7, None, 1, "Keyed shafting, 5/8 in x 72 in, 1018 cold-drawn, 3/16 in keyway: cut 3 x 403 mm + 1 x 427 mm (the drive shaft)",
     "Surplus Center", "601881", f"{SC}/5-8-x-72-keyed-shafting-3-16-wide-keyway/", 43.90, V, (5,), "Shafts"),
    (8, ("flange_bearing",), None, "2-bolt stamped-steel flange bearing SBSFL202-10: 5/8 in bore, set screws, 2-1/2 in bolt centres, 1/4 in bolts",
     "Surplus Center", "600174", f"{SC}/5-8-2-bolt-stamped-steel-flange-bearing/", 11.30, V, (4,), "Shafts"),
    (9, None, 1, "Key stock 3/16 x 3/16 in, 12 in (keys for the 4 front sprockets and the 15T on the shaft)", "any (hardware store, McMaster)", "",
     "", 4.00, E, (5, 6), "Shafts"),
    (10, ("bolt_m6x25",), None, "Hex bolt 1/4-20 x 1 in + nylock nut (bearings to the side plates)", "BoltsAndNuts.com / McMaster", "", "",
     0.30, E, (4,), "Shafts"),
    # ---- drive
    (11, ("nema34",), None, "NEMA 34 closed-loop stepper 34HS59-6004D-E1000, 12 N*m, 6 A, 14 mm x 37 mm keyed shaft",
     "StepperOnline", "34HS59-6004D-E1000",
     "https://www.omc-stepperonline.com/s-series-nema-34-closed-loop-stepper-motor-12-0-nm-1699-68oz-in-encoder-1000ppr-4000cpr-34hs59-6004d-e1000",
     0.0, "already bought by UofU", (6,), "Drive"),
    (12, ("cl86t",), None, "Closed-loop stepper driver CL86T V4.1 (24-80 VDC, 5 V/24 V logic selector)", "StepperOnline (OzRobotics)",
     "CL86T", "https://ozrobotics.com/shop/closed-loop-stepper-driver-v4-1-08-2a-2480vdc-for-nema-34-stepper-motor/", 47.43, V10,
     (11,), "Drive"),
    (13, ("lrs350",), None, "Power supply Mean Well LRS-350-48 (48 V, 7.3 A)", "TRC Electronics", "LRS-350-48",
     "https://www.trcelectronics.com/products/mean-well-lrs-350-48", 36.11, V10, (11,), "Drive"),
    (14, ("m5x25_shcs",), None, "M5 x 25 socket head screw + nylock nut (motor flange to the back plate, in slots)", "BoltsAndNuts.com / McMaster",
     "", "", 0.30, E, (6,), "Drive"),
    # ---- frame
    (15, None, 1, "2020 T-slot extrusion, 10 x 1000 mm pack: 4 posts of 541 mm, 4 long rails of 417.7 mm, 4 cross rails of 204 mm (5 bars)",
     "VEVOR", "2020OBLXC10JMQNSK001V0",
     "https://www.vevor.com/linear-guide-rail-c_10531/10pcs-39-4in-1000mm-t-slot-2020-aluminum-extrusion-anodized-linear-rail-p_010731760492",
     66.90, f"{V}; the page shows both in and out of stock", (1, 2), "Frame"),
    (16, ("corner_bracket",), None, "2020 90-degree corner bracket", "West3D", "NA0394",
     "https://west3d.com/products/angle-corner-connector-90-degree-like-openbuilds", 1.59, V, (2,), "Frame"),
    (17, None, 32, "M5 x 10 button head screw for the brackets (2 per bracket)", "West3D", "LDO3385M5X",
     "https://west3d.com/products/ldo-black-screws-nuts-and-various-fasteners-black", 1.99 / 50, f"50-pack $1.99; {V10}", (2,), "Frame"),
    (18, ("tnut_m5",), None, "M5 drop-in T-nut, 2020 slot 6 (brackets, side plates, feet)", "West3D", "WES5240M5",
     "https://west3d.com/products/roll-in-drop-in-t-nuts-for-2020-extrusions-m3-3mm-and-m5-5mm-threads", 0.17, V, (1, 2, 3), "Frame"),
    (19, ("foot",), None, "Leveling foot, M5 stud, into a T-nut in the base rail's bottom slot", "Amazon", "",
     "https://www.amazon.com/s?k=m5+leveling+feet+2020+extrusion", 2.0, E, (1,), "Frame"),
    (20, ("side_plate_front", "side_plate_back"), None,
     "Side plates, 1/4 in 6061: front 244 x 375 mm, back 244 x 485 mm, both from one 12 x 36 in plate; cut and drilled from dxf/ (BYU shop, or SendCutSend: price on upload)",
     "FixSupply (thyssenkrupp)", "SHT-6061-0.25X12-36",
     "https://fixsupply.com/1248-12-36-6061-aluminum-plate-t651-1-4-thick-x-12-wide-x-36-long", 104.89 / 2, f"one plate $104.89 for both; {V}",
     (3,), "Frame"),
    (21, ("m5x12_bhcs",), None, "M5 x 12 button head screw (side plates to the posts' T-nuts)", "BoltsAndNuts.com / McMaster", "", "", 0.12, E,
     (3,), "Frame"),
    # ---- fasteners
    (22, ("m3x6_bhcs",), None, "M3 x 6 button head screw (carriage to each A-1 tab)", "BoltsAndNuts.com / McMaster", "", "", 0.10, E, (8,),
     "Fasteners"),
    (23, ("insert_m3",), None, "M3 x 4 heat-set insert (CNC Kitchen short), two per carriage", "West3D", "",
     "https://west3d.com/products/cnc-kitchen-heat-set-inserts-various-sizes", 0.15, E, (8,), "Fasteners"),
    (24, ("m5x10_fhcs",), None, "M5 x 10 flat head (countersunk) screw: hinge pins, two per module", "BoltsAndNuts.com / McMaster", "", "",
     0.12, E, (10,), "Fasteners"),
    (25, ("m5x16_shcs",), None, "M5 x 16 socket head screw (hold-downs, through the side plates)", "BoltsAndNuts.com / McMaster", "", "", 0.20,
     E, (9,), "Fasteners"),
    (26, ("insert_m5",), None, "M5 heat-set insert (hold-downs)", "West3D", "", "https://west3d.com/products/cnc-kitchen-heat-set-inserts-various-sizes",
     0.30, E, (9,), "Fasteners"),
    (27, ("m5x10_shcs",), None, "M5 x 10 socket head screw (tensioner blocks, into tapped holes in the plates)", "BoltsAndNuts.com / McMaster",
     "", "", 0.15, E, (4,), "Fasteners"),
    (28, ("m5x30_shcs",), None, "M5 x 30 socket head screw + hex nut (tensioner jack screws)", "BoltsAndNuts.com / McMaster", "", "", 0.30, E,
     (4,), "Fasteners"),
    # ---- printed parts
    (29, ("carriage",), None, "Carriage, PETG (H2D, on the bed's diagonal; about 100 g each)", "printed", "stl/carriage.stl", "", 2.0,
     "filament at $20/kg", (8,), "Printed"),
    (30, ("hold_down", "tensioner_block"), None, "Hold-downs (2) and tensioner blocks (4), PETG", "printed",
     "stl/hold_down.stl, stl/tensioner_block.stl", "", 0.4, "filament", (4, 9), "Printed"),
    (31, ("auger_blank",), None, "Auger blank, PETG (the auger's outside, hollow; fill with salt to about 200 g per module)", "printed",
     "stl/auger_blank.stl", "", 1.0, "filament", (10,), "Printed"),
    (32, None, 12, "Mounting plate (Sam's Oct 8 Onshape part) and auger cap (PR #170), printed for modules 2-13", "printed",
     "Onshape 581956d5; reference/auger-cap-threaded.step", "", 0.8, "filament", (10,), "Printed"),
    # ---- sensing & electronics
    (33, ("hall_switch",), None, "Hall-effect switch US5881 (unipolar, open drain, TO-92): INDEX and HOME", "Adafruit", "158",
     "https://www.adafruit.com/product/158", 2.00, V10, (9,), "Electronics"),
    (34, ("magnet",), None, "Neodymium disc magnet D42-N52, 1/4 x 1/8 in (13 index + 1 home)", "K&J Magnetics", "D42-N52",
     "https://www.kjmagnetics.com/d42-n52-neodymium-disc-magnet", 0.52, V10, (8,), "Electronics"),
    (35, ("raspberry_pi",), None, "Raspberry Pi Zero 2 W (or any spare Pi that runs pigpio)", "Adafruit", "5291",
     "https://www.adafruit.com/product/5291", 15.00, E, (11,), "Electronics"),
    (36, ("perfboard",), None, "Interface board: 74AHCT125 (3.3 V GPIO to 5 V step/dir/enable), 3 x 10k pull-ups to 3.3 V, screw terminals, perfboard",
     "Adafruit", "1787", "https://www.adafruit.com/product/1787", 6.0, E, (11,), "Electronics"),
    (37, ("estop",), None, "E-stop GCX1136 (22 mm, NC, twist to release) + enclosure; breaks the 48 V feed to the driver",
     "AutomationDirect", "GCX1136", "https://www.automationdirect.com/pn/GCX1136", 30.0, f"$21 + $9 box; {V10}", (11,), "Electronics"),
    (38, ("board_panel",), None, "Electronics board, 1/4 in plywood 420 x 300", "Home Depot", "", "", 6.0, E, (11,), "Electronics"),
    (39, None, 1, "IEC C14 inlet with switch + fuse drawer (Qualtek 719W-UEL3BR51)", "Digi-Key", "719W-UEL3BR51",
     "https://www.digikey.com/en/products/detail/qualtek/719W-UEL3BR51/23019206", 7.66, V10, (11,), "Electronics"),
    (40, None, 1, "18 AWG stranded hook-up wire, 25 ft (48 V and motor)", "Digi-Key", "18UL1007STRBLA25",
     "https://www.digikey.com/en/products/result?keywords=18UL1007STRBLA25", 14.57, V10, (11,), "Electronics"),
    # ---- module 1 and the station's electronics carriage (exist already in the lab)
    (41, None, 1, "Module 1: mounting plate (Sam's Oct 8 Onshape design), printed", "lab", "Onshape 581956d5",
     "https://cad.onshape.com/documents/581956d5528927957a4c0b98/w/5778b22212c6736ada520515/e/24d73974055f92c0f2fa292f",
     0.0, "existing", (10,), "Module"),
    (42, None, 1, "Module 1: auger, threaded storage, and cap (lab design, PR #170)", "lab", "reference/auger-*.step", "", 0.0, "existing",
     (10,), "Module"),
    (43, ("sam_electronics_carriage",), None, "Electronics carriage (Sam's Oct 8), shown docked at the station for reference", "lab",
     "Onshape 581956d5", "", 0.0, "existing", (10,), "Module"),
    # ---- test equipment (not in CAD)
    (44, None, 1, "Digital indicator 0-1 in / 0.01 mm with arm and magnetic base (index, lift, sag tests)", "Penn Tool Co",
     "iGaging 35-520", "https://www.penntoolco.com/igaging-digital-indicator-universal-arm-magnetic-base-set-35-520", 119.95, V10,
     (12,), "Test"),
    (45, None, 1, "Digital hanging scale 50 kg (torque lever, push-up and snap forces; a 50 N push-pull gauge is better if the lab has one)",
     "Etekcity", "EL11", "https://etekcity.com/products/luggage-scale-el11", 10.99, V10, (12,), "Test"),
    (46, None, 1, "ADXL343 accelerometer breakout (transit vibration)", "Adafruit", "4097", "https://www.adafruit.com/product/4097",
     5.95, V10, (12,), "Test"),
    (47, None, 3, "Table salt, 26 oz (fills the 12 auger blanks to working mass)", "grocery", "", "", 1.5, E, (12,), "Test"),
]


# lines you can only buy in packs larger than the rig uses: what you actually pay
BUY = {20: 104.89}

NOTES = """**Before cutting the chain, measure it.** ANSI #35 has a 0.200 in (5.08 mm) bushing and 0.188 in (4.78 mm) between the
inner plates. ISO 06B has the same 3/8 in pitch but a 6.35 mm roller and 5.72 mm between the plates, and the two don't mix.
(ISO 06C *is* ANSI 35.) The 3 ft box already on the ME order is 96 links, 8 short of one v2 loop: keep it as spares.

**A-1 links: Nitro's hole is 0.133 in (M3), Red Boar's is 0.10 in (M2.5).** The carriage takes M3 inserts. If you buy Red
Boar's instead (25-pack $92.76), use M2.5 x 6 screws and M2.5 inserts, or drill the tabs to 3.2 mm.

**Sprocket phase.** On each shaft, key the front sprocket and leave the back one's key out. Bolting the carriages across
both chains (step 8) sets the back sprocket's phase. Then lock it with both set screws on the round of the shaft and spot a
dimple under each one. A 32T tooth is 11.25 deg, so a keyed back sprocket would land up to 4.8 mm out of step.

**Shafts are keyed 1018, not hardened**, so the set screws bite. Cutting 3 x 403 + 427 mm from 72 in leaves about 190 mm.

**Shop work:** cut and drill the two side plates from `dxf/` (or upload the DXFs to SendCutSend for a quote); re-bore the
motor's 15T sprocket from 1/2 in to 14 mm H7 and broach a 5 mm keyway; tap the eight M5 holes for the tensioner blocks.

**Prices** are as listed on 2026-10-13 by vendor (`verified`); lines carried over from the v1 BoM were verified on
2026-10-10; generic hardware is `estimate`. USA Roller Chain still has a $300 web minimum, which is why the sprockets come
from Surplus Center."""


def counted() -> Counter:
    import layout
    return Counter(p.key for p in layout.placements())


def rows() -> list[dict]:
    n = counted()
    out = []
    for item, keys, qty, desc, vendor, pn, url, price, pack, steps, cat in ITEMS:
        q = sum(n[k] for k in keys) if keys else qty
        if item == 18:
            q = n["tnut_m5"] + 2 * n["corner_bracket"]
        if item == 17:
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
