"""Bill of materials for the chain-carousel test rig v2 (vertical twin chain).

ITEMS is the single table: item number, what, where to buy it, price, and
which assembly step uses it. Quantities of modelled parts are counted from
layout.placements(), so the BoM and the CAD cannot drift apart; unmodelled
items (wire, tools, test gear) carry their own quantity.

    python bom.py        # writes bom.csv and prints the totals
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (item, keys counted from the CAD or None, qty if not counted, description,
#  vendor, part number, url, unit price USD, price source, steps, category)
V = "verified 2026-10-18"
V16 = "verified 2026-10-16 (paternoster BoM)"
V13 = "verified 2026-10-13"
V10 = "verified 2026-10-10 (v1 BoM)"
E = "estimate, not verified"
SC = "https://www.surpluscenter.com"
MC = "https://www.mcmaster.com"
NITRO_A1 = "https://www.nitrochain.com/35-a1-standard-attachment-connecting-link"

ITEMS = [
    # ---- chain & sprockets
    (1, None, 1, "ANSI #35 roller chain, 10 ft roll (320 pitches): two 104-link loops + the 44-link drive chain",
     "Nitro Chain", "RC35-1R-10FT", "https://www.nitrochain.com/35-roller-chain-10ft", 23.53, V13, (6, 7), "Chain"),
    (2, ("chain_a1",), None, "#35 A-1 attachment connecting link, spring clip, 0.133 in hole (M3): 13 per chain",
     "Nitro Chain", "CL35-A1", NITRO_A1, 2.55, V13, (7,), "Chain"),
    (3, None, 1, "Spring clips for #35 connecting links, pack of 5 (spares)", "McMaster-Carr", "5501N12", f"{MC}/5501N12/", 4.60, V16, (7,), "Chain"),
    (4, None, 1, "Roller chain breaker, #25-#60 (Dura-Roll #1)", "Surplus Center", "100115",
     "https://surpluscenter.com/1-roller-chain-breaker-for-25-60-pitch/", 17.20, V13, (6, 7), "Tools"),
    (5, ("sprocket_32",), None, "Sprocket 35BS32-5/8: 32T, type B, 2 in hub, 7/8 in through the bore, 5/8 in bore, 3/16 in keyway, 2 set screws",
     "Surplus Center", "601139", f"{SC}/32t-5-8-bore-35p-sprocket/", 21.55, V16, (5,), "Chain"),
    (6, ("sprocket_15_shaft",), None, "Sprocket 35BS15H-5/8: 15T, 5/8 in bore (drive chain, on the B+ shaft's stub)",
     "Surplus Center", "601078", f"{SC}/15t-5-8-bore-35p-sprocket/", 6.65, V13, (6,), "Chain"),
    (7, ("sprocket_15_motor",), None, "Sprocket 35BS15H-1/2: 15T, 1/2 in bore; shop re-bores it to 14 mm H7 with a 5 mm keyway for the NEMA 34",
     "Surplus Center", "601077", f"{SC}/15t-1-2-bore-35p-sprocket/", 6.65, V13, (6,), "Chain"),
    # ---- shafts & bearings
    (8, None, 1, "Keyed shafting, 5/8 in x 72 in, 1018, 3/16 in keyway: cut 3 x 403 mm + 1 x 427 mm (the drive shaft)",
     "Surplus Center", "601881", f"{SC}/5-8-x-72-keyed-shafting-3-16-wide-keyway/", 43.90, V16, (5,), "Shafts"),
    (9, ("flange_bearing",), None, "2-bolt stamped-steel flange bearing SBSFL202-10: 5/8 in bore, set screws, 2-1/2 in bolt centres",
     "Surplus Center", "600174", f"{SC}/5-8-2-bolt-stamped-steel-flange-bearing/", 11.30, V16, (4,), "Shafts"),
    (10, None, 1, "Key stock 3/16 x 3/16 in, 12 in (front sprockets and the 15T on the shaft; back sprockets locked by set screws after phasing)",
     "Surplus Center", "G&G 407-0300", "https://surpluscenter.com/3-16-square-key-stock-12-length-g-g-mfg-407-", 2.80, V16, (5, 6), "Shafts"),
    (11, ("bolt_m6x25",), None, "Hex bolt 1/4-20 x 1 in, Grade 5 (flange bearings to the side plates)", "PaulB Hardware", "H5C14X1",
     "https://paulbhardware.com/hex-cap-screw-1-4-20x1-gr5-zinc-h5c14x1", 0.15, V16, (4,), "Shafts"),
    (12, None, 1, "1/4-20 nylon-insert locknuts, pack of 100 (16 used on the bearings)", "McMaster-Carr", "95615A120", f"{MC}/95615A120/",
     7.46, V16, (4,), "Shafts"),
    # ---- drive
    (13, ("nema34",), None, "NEMA 34 closed-loop stepper 34HS59-6004D-E1000, 12 N*m, 14 mm x 37 mm keyed shaft",
     "StepperOnline", "34HS59-6004D-E1000",
     "https://www.omc-stepperonline.com/s-series-nema-34-closed-loop-stepper-motor-12-0-nm-1699-68oz-in-encoder-1000ppr-4000cpr-34hs59-6004d-e1000",
     0.0, "already bought by UofU", (6,), "Drive"),
    (14, ("cl86t",), None, "Closed-loop stepper driver CL86T V4.1 (lab has one from the UofU order)", "StepperOnline (OzRobotics)", "CL86T",
     "https://ozrobotics.com/shop/closed-loop-stepper-driver-v4-1-08-2a-2480vdc-for-nema-34-stepper-motor/", 0.0,
     "in the lab (47.43 new, verified 2026-10-16)", (11,), "Drive"),
    (15, ("lrs350",), None, "Power supply Mean Well LRS-350-48 (48 V, 7.3 A)", "TRC Electronics", "LRS-350-48",
     "https://www.trcelectronics.com/products/mean-well-lrs-350-48", 36.11, V16, (11,), "Drive"),
    (16, ("m5x25_shcs",), None, "M5 x 25 socket head screw (motor flange to the back plate, in slots)", "BelMetric", "M5 x 25 SHCS",
     "https://www.belmetric.com/", 0.20, E, (6,), "Drive"),
    (17, ("nut_m5",), None, "M5 nylon-insert locknut (4 on the motor, 4 trapped in the tensioner blocks as jack-screw nuts)", "McMaster-Carr",
     "93625A200", f"{MC}/93625A200/", 0.12, E, (4, 6), "Drive"),
    # ---- frame
    (18, None, 1, "2020 T-slot extrusion, 10 x 1000 mm pack: 4 posts of 676 mm (each offcut gives a 204 mm cross rail), "
     "4 long rails of 417.7 mm (2 per bar), station rail 204 + fork post 194 + vial post 197 from a seventh bar",
     "VEVOR", "2020OBLXC10JMQNSK001V0",
     "https://www.vevor.com/linear-guide-rail-c_10531/10pcs-39-4in-1000mm-t-slot-2020-aluminum-extrusion-anodized-linear-rail-p_010731760492",
     66.90, f"{V13}; the page shows both in and out of stock", (1, 2, 8), "Frame"),
    (19, ("corner_bracket",), 2, "2020 90-degree corner bracket (+2 for the fork and vial posts)", "West3D", "NA0394",
     "https://west3d.com/products/angle-corner-connector-90-degree-like-openbuilds", 1.59, V13, (1, 2, 8), "Frame"),
    (20, None, 50, "M5 x 10 button head screw, with blue threadlocker (brackets and station parts; T-nuts can't take a nylock)", "BelMetric",
     "M5 x 10 BHCS", "https://www.belmetric.com/", 0.12, V16, (1, 2, 8), "Frame"),
    (21, ("tnut_m5",), 50, "M5 drop-in T-nut, 2020 slot 6 (brackets, side plates, feet, station)", "West3D", "WES5240M5",
     "https://west3d.com/products/roll-in-drop-in-t-nuts-for-2020-extrusions-m3-3mm-and-m5-5mm-threads", 0.17, V13, (1, 2, 3, 8), "Frame"),
    (22, ("foot",), None, "Leveling foot, M6 x 40 stud, into a T-nut in the base rail", "TNUTZ", "LF-020-A", "https://www.tnutz.com/product/lf-020-a/",
     1.85, V16, (1,), "Frame"),
    (23, ("side_plate_front", "side_plate_back"), None,
     "Side plates, 1/4 in 6061: front 244 x 375 mm, back 244 x 485 mm, both from one 12 x 36 in plate; cut and drilled from dxf/ "
     "(BYU shop, or SendCutSend: price on upload)", "FixSupply (thyssenkrupp)", "SHT-6061-0.25X12-36",
     "https://fixsupply.com/1248-12-36-6061-aluminum-plate-t651-1-4-thick-x-12-wide-x-36-long", 104.89 / 2,
     f"one plate $104.89 for both; {V13}", (3,), "Frame"),
    (24, ("m5x12_bhcs",), None, "M5 x 12 button head screw (side plates to the posts' T-nuts), with blue threadlocker", "BelMetric", "M5 x 12 BHCS",
     "https://www.belmetric.com/", 0.12, E, (3,), "Frame"),
    (25, None, 1, "Loctite 243 (blue, medium strength) for T-nut screws, set screws and the tensioner blocks' screws; Loctite 222 "
     "(purple, low strength) where a part is meant to come apart", "McMaster-Carr", "Loctite 243", f"{MC}/loctite/", 27.25, V16, (1,), "Frame"),
    # ---- fasteners
    (26, ("m3x12_bhcs",), None, "M3 x 12 button head screw (carriage to each A-1 tab, from the outside)", "BelMetric", "M3 x 12 BHCS",
     "https://www.belmetric.com/", 0.10, E, (10,), "Fasteners"),
    (27, None, 1, "M3 nylon-insert locknut, 18-8, pack of 100 (one in each carriage hook; the actuator's clevis pins)", "McMaster-Carr",
     "93625A100", f"{MC}/93625A100/", 6.94, V16, (9, 10), "Fasteners"),
    (28, ("clevis_pin",), 4, "Clevis pin 5 mm with retaining-ring groove, steel, about 14 mm usable length (module hinge pins, 2 per module; 4 spare)",
     "McMaster-Carr", "clevis pins, metric", f"{MC}/clevis-pins/", 0.65, E, (9,), "Fasteners"),
    (29, ("eclip",), 10, "E-clip DIN 6799 for a 4 mm groove (5 mm pin), steel (on the hinge pins; 10 spare)", "McMaster-Carr",
     "e-style retaining rings, metric", f"{MC}/e-style-retaining-rings/", 0.10, E, (9,), "Fasteners"),
    (30, ("m3x6_fhcs",), None, "M3 x 6 flat head screw (steel armature tab to the plate)", "BelMetric", "M3 x 6 FHCS", "https://www.belmetric.com/",
     0.10, E, (9,), "Fasteners"),
    (31, ("insert_m3",), None, "M3 x 4 heat-set insert (CNC Kitchen short): two per mounting plate, for the armature tab", "West3D", "",
     "https://west3d.com/products/cnc-kitchen-heat-set-inserts-various-sizes", 0.15, E, (9,), "Fasteners"),
    (32, ("m5x16_shcs",), None, "M5 x 16 socket head screw (hold-downs, through the side plates), with blue threadlocker", "BelMetric",
     "M5 x 16 SHCS", "https://www.belmetric.com/", 0.20, E, (8,), "Fasteners"),
    (33, None, 1, "M5 brass heat-set insert, 5.7 mm long, 6.4 mm hole, pack of 25 (hold-downs)", "McMaster-Carr", "94459A774", f"{MC}/94459A774/",
     7.27, V16, (8,), "Fasteners"),
    (34, ("m5x10_shcs",), None, "M5 x 10 socket head screw (tensioner blocks, into tapped holes in the plates)", "BelMetric", "M5 x 10 SHCS",
     "https://www.belmetric.com/", 0.15, E, (4,), "Fasteners"),
    (35, ("m5x30_shcs",), None, "M5 x 30 socket head screw (tensioner jack screws)", "BelMetric", "M5 x 30 SHCS", "https://www.belmetric.com/",
     0.25, E, (4,), "Fasteners"),
    # ---- printed parts
    (36, ("carriage",), None, "Carriage, PETG, with the two tab hooks (H2D, on the bed's diagonal; about 100 g each)", "printed", "stl/carriage.stl",
     "", 2.0, "filament at $20/kg", (10,), "Printed"),
    (37, ("hold_down", "tensioner_block"), None, "Hold-downs (2) and tensioner blocks (4), PETG", "printed", "stl/hold_down.stl, stl/tensioner_block.stl",
     "", 0.4, "filament", (4, 8), "Printed"),
    (38, ("clevis_bracket", "station_yoke", "fork", "fork_arm", "vial_cup", "vial_funnel", "magnet_bracket"), None,
     "Station parts, PETG: actuator base clevis, yoke, approach fork and arm, vial cup, D-cut funnel, dock magnet bracket", "printed", "stl/",
     "", 0.5, "filament", (8,), "Printed"),
    (39, ("sam_mounting_plate",), -1, "Mounting plate (Sam's Oct 13 Onshape part), printed for modules 2-13 (module 1 exists)", "printed",
     "Onshape 581956d5", "https://cad.onshape.com/documents/581956d5528927957a4c0b98/w/5778b22212c6736ada520515/e/24d73974055f92c0f2fa292f",
     1.40, "filament at $20/kg", (9,), "Printed"),
    # ---- station
    (40, ("actuator_body",), None, "Actuonix P16-150-22-12-P linear actuator: 150 mm stroke, potentiometer feedback, 46 mm/s, 50 N",
     "Actuonix", "P16-150-22-12-P", "https://www.actuonix.com/p16-p", 90.0, V16, (8,), "Station"),
    (41, None, 1, "Actuonix LAC linear actuator control board (closed-loop position from the pot; USB, RC, PWM or 0-3.3 V in)", "Actuonix", "LAC",
     "https://www.actuonix.com/lac", 30.0, V16, (8,), "Station"),
    (42, None, 1, "12 V supply for the LAC and actuator", "Actuonix", "12V PSU", "https://www.actuonix.com/lac", 10.0, V16, (8,), "Station"),
    (43, None, 1, "Shoulder screw 4 x 30 mm, M3 (actuator's rear clevis) + M3 locknut", "McMaster-Carr", "90265A992", f"{MC}/90265A992/", 5.11, V16,
     (8,), "Station"),
    (44, None, 1, "Shoulder screw 4 x 20 mm, M3 (rod end in the yoke) + M3 locknut", "McMaster-Carr", "90265A124", f"{MC}/90265A124/", 5.68, V16,
     (8,), "Station"),
    (45, ("dock_magnet",), None, "Holding electromagnet P20/15, 5 V, 0.22 A, 2.5 kg (24.5 N) at zero gap: the dock's mesh preload", "Adafruit", "3872",
     "https://www.adafruit.com/product/3872", 7.50, V, (8,), "Station"),
    (46, None, 1, "N-channel logic-level MOSFET IRLB8721 (switches the dock magnet from the carriage board; out of stock on 2026-10-18, any "
     "logic-level N-MOSFET such as FQP30N06L works)", "Adafruit", "355", "https://www.adafruit.com/product/355", 2.25, V, (8,), "Station"),
    (47, None, 1, "1N4001 diode, 10-pack (flyback across the magnet coil)", "Adafruit", "755", "https://www.adafruit.com/product/755", 1.50, V, (8,),
     "Station"),
    (48, ("armature_tab",), None, "Armature tab, low-carbon steel 2 mm (14 ga), 22 x 28 mm, two countersunk M3 holes: laser cut", "SendCutSend",
     "dxf (from parts.armature_tab)", "https://sendcutsend.com/", 3.50, "estimate (SendCutSend quotes on upload)", (9,), "Station"),
    (49, ("load_cell",), None, "Load cell 100 g (TAL221) under the vial", "SparkFun", "SEN-14727", "https://www.sparkfun.com/products/14727", 14.50,
     V16, (8,), "Station"),
    (50, None, 1, "HX711 load-cell amplifier", "SparkFun", "SEN-13879", "https://www.sparkfun.com/products/13879", 4.95, V16, (8,), "Station"),
    (51, ("vial",), None, "20 mL glass scintillation vial (lab stock; Wheaton 986546 is $383.77 per 500)", "lab / pfstar.com", "986546",
     "https://pfstar.com/986546-20-mL-LS-Vial-22-400-Urea-Cap-PE-Cone-Ln", 0.77, V16, (8,), "Station"),
    (52, ("sam_electronics_carriage",), None, "Electronics carriage (Sam's Oct 13) with the doser's NEMA 11 and 12 V solenoid", "lab",
     "Onshape 581956d5", "", 0.0, "existing (doser parts)", (8,), "Station"),
    # ---- sensing & electronics
    (53, ("hall_switch",), None, "Hall-effect switch US5881 (unipolar, open drain, TO-92): INDEX and HOME", "Adafruit", "158",
     "https://www.adafruit.com/product/158", 2.00, V10, (8,), "Electronics"),
    (54, ("magnet",), None, "Neodymium disc magnet D42-N52, 1/4 x 1/8 in (13 index + 1 home)", "K&J Magnetics", "D42-N52",
     "https://www.kjmagnetics.com/d42-n52-neodymium-disc-magnet", 0.52, V10, (10,), "Electronics"),
    (55, ("raspberry_pi",), None, "Raspberry Pi Zero 2 W (or any spare Pi that runs pigpio)", "Adafruit", "5291",
     "https://www.adafruit.com/product/5291", 15.00, E, (11,), "Electronics"),
    (56, ("perfboard",), None, "Interface board: 74AHCT125 (3.3 V GPIO to 5 V step/dir/enable), 3 x 10k pull-ups, screw terminals, perfboard",
     "Adafruit", "1787", "https://www.adafruit.com/product/1787", 6.0, E, (11,), "Electronics"),
    (57, ("estop",), None, "E-stop GCX1136 (22 mm, NC, twist to release) + enclosure; breaks the 48 V feed to the driver",
     "AutomationDirect", "GCX1136", "https://www.automationdirect.com/pn/GCX1136", 30.0, f"$21 + $9 box; {V10}", (11,), "Electronics"),
    (58, ("board_panel",), None, "Electronics board, 1/4 in plywood 420 x 300", "Home Depot", "", "", 6.0, E, (11,), "Electronics"),
    (59, None, 1, "IEC C14 inlet with switch + fuse drawer (Qualtek 719W-UEL3BR51)", "Digi-Key", "719W-UEL3BR51",
     "https://www.digikey.com/en/products/detail/qualtek/719W-UEL3BR51/23019206", 7.66, V10, (11,), "Electronics"),
    (60, None, 1, "18 AWG stranded hook-up wire, 25 ft (48 V and motor)", "Digi-Key", "18UL1007STRBLA25",
     "https://www.digikey.com/en/products/result?keywords=18UL1007STRBLA25", 14.57, V10, (11,), "Electronics"),
    # ---- modules (exist in the lab)
    (61, ("auger",), None, "Auger, threaded storage (44T gear), and cap, lab design (PR #170): 13 from #134's batch of 16", "lab",
     "reference/auger-*.step", "", 0.0, "existing", (9,), "Module"),
    # ---- test equipment (not in CAD)
    (62, None, 1, "Digital indicator 0-1 in / 0.01 mm with arm and magnetic base (index, lift, sag tests)", "Penn Tool Co",
     "iGaging 35-520", "https://www.penntoolco.com/igaging-digital-indicator-universal-arm-magnetic-base-set-35-520", 119.95, V10,
     (12,), "Test"),
    (63, None, 1, "Digital hanging scale 50 kg (torque lever, push-up and snap forces; a 50 N push-pull gauge is better if the lab has one)",
     "Etekcity", "EL11", "https://etekcity.com/products/luggage-scale-el11", 10.99, V10, (12,), "Test"),
    (64, None, 1, "ADXL343 accelerometer breakout (transit vibration)", "Adafruit", "4097", "https://www.adafruit.com/product/4097",
     5.95, V10, (12,), "Test"),
    (65, None, 3, "Table salt, 26 oz (test fill for the augers)", "grocery", "", "", 1.5, E, (12,), "Test"),
]

# lines you can only buy in packs larger than the rig uses: what you actually pay
BUY = {23: 104.89}

NOTES = """**Before cutting the chain, measure it.** ANSI #35 has a 0.200 in (5.08 mm) bushing and 0.188 in (4.78 mm) between the
inner plates. ISO 06B has the same 3/8 in pitch but a 6.35 mm roller and 5.72 mm between the plates, and the two don't mix.
(ISO 06C *is* ANSI 35.) The 3 ft box already on the ME order is 96 links, 8 short of one v2 loop: keep it as spares.

**A-1 links: Nitro's hole is 0.133 in (M3).** The M3 x 12 screw goes in from the carriage's outer face, through the tab, into
a nylon-insert locknut held in the carriage's printed hook under the tab.

**Sprocket phase.** On each shaft, key the front sprocket and leave the back one's key out. Bolting the carriages across
both chains (step 10) sets the back sprocket's phase. Then lock it with both set screws on the round of the shaft and spot a
dimple under each one (Loctite 243 on every set screw). A 32T tooth is 11.25 deg, so a keyed back sprocket would land up to
4.8 mm out of step.

**Vibration.** Every nut on the machine is a nylon-insert locknut: bearings, motor, carriage tabs, jack screws, actuator pins.
Screws into T-nuts, heat-set inserts and tapped holes get Loctite 243; the hinge pins are retained by e-clips.

**Shop work:** cut and drill the two side plates from `dxf/` (or upload the DXFs to SendCutSend for a quote); re-bore the
motor's 15T sprocket from 1/2 in to 14 mm H7 and broach a 5 mm keyway; tap the eight M5 holes for the tensioner blocks;
face the steel pinion's hub off (KHK SS1-20A) so it fits in front of the dock magnet; laser cut the 13 steel armature tabs
and the two yoke arms.

**Prices** are as listed on the date shown on each line. McMaster asked for a login on 2026-10-18, so McMaster lines are
carried from the paternoster BoM (read logged out on 2026-10-16) or marked estimate. Generic hardware is `estimate`."""


def counted() -> Counter:
    import layout
    return Counter(p.key for p in layout.placements())


def rows() -> list[dict]:
    n = counted()
    out = []
    for item, keys, qty, desc, vendor, pn, url, price, pack, steps, cat in ITEMS:
        q = sum(n[k] for k in keys) + (qty or 0) if keys else qty
        ext = BUY.get(item, q * price)
        out.append(dict(item=item, qty=q, description=desc, vendor=vendor, part_number=pn, url=url,
                        unit_usd=round(price, 2), ext_usd=round(ext, 2), pack=pack,
                        steps=",".join(map(str, steps)), category=cat, keys=",".join(keys or ())))
    return out


def totals(rs: list[dict]) -> dict:
    t = sum(r["ext_usd"] for r in rs)
    test = sum(r["ext_usd"] for r in rs if r["category"] == "Test")
    est = sum(r["ext_usd"] for r in rs if r["pack"].startswith("estimate"))
    return dict(total=round(t, 2), without_test=round(t - test, 2), estimated=round(est, 2))


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
    t = totals(rs)
    print(f"{len(rs)} lines, total ${t['total']:.2f} (without test gear ${t['without_test']:.2f}; estimated lines ${t['estimated']:.2f})")


if __name__ == "__main__":
    write()
