"""Bill of materials for the paternoster carousel.

ITEMS is the single table: item number, what, where to buy it, price, and
which assembly step uses it. Quantities of modelled parts are counted from
layout.placements(), so the BoM and the CAD cannot drift apart; unmodelled
items (wire, tools, test gear) carry their own quantity.

    python bom.py        # writes bom.csv and prints the totals
"""
from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

V = "verified 2026-10-16"
V13 = "verified 2026-10-13 (v2 BoM)"
V10 = "verified 2026-10-10 (v1 BoM)"
E = "estimate, not verified"
SC = "https://www.surpluscenter.com"
MC = "https://www.mcmaster.com"

# (item, keys counted from the CAD or None, qty if not counted, description,
#  vendor, part number, url, unit price USD, pack size (units per price), source note, steps, category)
ITEMS = [
    # ---- chain & sprockets
    (1, None, 1, "ANSI #35 roller chain, 10 ft roll (320 pitches): two 120-link loops use 216 plain pitches + the 24 SA-1 links",
     "Nitro Chain", "RC35-1R-10FT", "https://www.nitrochain.com/35-roller-chain-10ft", 23.53, 1, V, (6,), "Chain"),
    (2, ("chain_sa1",), None, "#35 SA-1 attachment connecting link, 0.134 in hole (M3 passes, no drilling), C1 0.375 in: 12 per chain (+2 spare)",
     "McMaster-Carr", "7321K31", f"{MC}/7321K31/", 3.13, 1, V, (6,), "Chain"),
    (3, None, 1, "Spring clips for #35 connecting links, pack of 5 (spares)", "McMaster-Carr", "5501N12", f"{MC}/5501N12/", 4.60, 1, V, (6,), "Chain"),
    (4, None, 1, "Roller chain breaker, #25-#60", "Surplus Center", "100115", "https://surpluscenter.com/1-roller-chain-breaker-for-25-60-pitch/",
     17.20, 1, V13, (6,), "Tools"),
    (5, ("sprocket_32", "sprocket_32_idler"), None,
     "Sprocket 35BS32-5/8: 32T, 2 in hub, 7/8 in through the bore. 4 for the bottom shafts (keyed); 4 re-bored to 35 mm H7 by the shop for two 6202s (top idlers)",
     "Surplus Center", "601139", f"{SC}/32t-5-8-bore-35p-sprocket/", 21.55, 1, V, (4, 5), "Chain"),
    # ---- shafts, bearings, idlers
    (6, None, 1, "Keyed shafting 5/8 in x 72 in, 3/16 in keyway: cut 1 x 435 mm and 1 x 463 mm (drive)", "Surplus Center", "601881",
     f"{SC}/5-8-x-72-keyed-shafting-3-16-wide-keyway/", 43.90, 1, V, (4,), "Shafts"),
    (7, ("flange_bearing",), None, "2-bolt stamped-steel flange bearing SBSFL202-10, 5/8 in bore, set screws (bottom shafts; only 24 in stock)",
     "Surplus Center", "600174", f"{SC}/5-8-2-bolt-stamped-steel-flange-bearing/", 11.30, 1, V, (3,), "Shafts"),
    (8, None, 1, "Key stock 3/16 x 3/16 in, 12 in (front sprockets keyed; back ones locked by set screws after phasing)", "Surplus Center",
     "G&G 407-0300", "https://surpluscenter.com/3-16-square-key-stock-12-length-g-g-mfg-407-", 2.80, 1, V, (4,), "Shafts"),
    (9, None, 1, "Metric key 5 x 5 mm (NEMA 34 shaft into the coupling hub)", "PaulB Hardware", "metric key stock",
     "https://paulbhardware.com/metric-key-stock", 1.09, 1, V, (7,), "Shafts"),
    (10, None, 1, "Deep-groove ball bearing 6202-2RS, 15 x 35 x 11, 10-pack (two per top idler; McMaster 5972K368 is $8.46 each)", "VXB",
     "6202-2RS 10-pack", "https://www.vxb.com/", 29.99, 1, V, (5,), "Shafts"),
    (11, None, 1, "1045 steel rod, 15 mm (-0.013/0), 1 ft: the shop turns four idler axles (31 mm seat, M10 stem; shoulder from a 22 mm washer)",
     "McMaster-Carr", "5615N15", f"{MC}/5615N15/", 25.12, 1, V, (5,), "Shafts"),
    (12, ("nut_m10",), None, "M10 nylon-insert locknut + DIN 125A washer (idler axles, outside the side plates)", "BelMetric", "M10 nylock + washer",
     "https://www.belmetric.com/", 0.38, 1, V, (5,), "Shafts"),
    (13, None, 8, "Hex bolt 1/4-20 x 1 in, Grade 5 (flange bearings to the side plates)", "PaulB Hardware", "H5C14X1",
     "https://paulbhardware.com/hex-cap-screw-1-4-20x1-gr5-zinc-h5c14x1", 0.15, 1, V, (3,), "Shafts"),
    (14, None, 1, "1/4-20 nylon-insert locknuts, pack of 100", "McMaster-Carr", "95615A120", f"{MC}/95615A120/", 7.46, 1, V, (3,), "Shafts"),
    # ---- drive
    (15, ("nema34",), None, "NEMA 34 closed-loop stepper 34HS59-6004D-E1000, 12 N*m, 14 mm keyed shaft (StepperOnline STEP from PR #115)",
     "StepperOnline", "34HS59-6004D-E1000", "https://www.omc-stepperonline.com/s-series-nema-34-closed-loop-stepper-motor-12-0-nm-1699-68oz-in-encoder-1000ppr-4000cpr-34hs59-6004d-e1000",
     0.0, 1, "already bought by UofU", (7,), "Drive"),
    (16, None, 2, "Jaw coupling hub L090, iron, keyed: one 14 mm bore (5 mm keyway), one 5/8 in bore (3/16 keyway)", "McMaster-Carr", "6408K14",
     f"{MC}/6408K14/", 21.35, 1, V, (7,), "Drive"),
    (17, None, 1, "Jaw coupling spider L090, Buna-N, 15.8 N*m (the L075's 10.2 N*m is under the motor's 12)", "McMaster-Carr", "6408K75",
     f"{MC}/6408K75/", 15.98, 1, V, (7,), "Drive"),
    (18, ("standoff",), None, "Round standoff 10 mm OD x 79 mm, M6 female both ends, aluminium (motor plate to the back plate) + 2 M6 x 12 screws each",
     "McMaster-Carr", "93330A", f"{MC}/standoffs/", 5.50, 1, E, (7,), "Drive"),
    (19, None, 4, "M5 x 16 socket head screw + M5 nylon-insert locknut (NEMA 34 flange to the motor plate)", "McMaster-Carr", "91292A126 + 93625A200",
     f"{MC}/93625A200/", 0.35, 1, E, (7,), "Drive"),
    (20, None, 1, "Closed-loop stepper driver CL86T V4.1 (lab has one from the UofU order)", "StepperOnline (OzRobotics)", "CL86T",
     "https://ozrobotics.com/shop/closed-loop-stepper-driver-v4-1-08-2a-2480vdc-for-nema-34-stepper-motor/", 0.0, 1, "in the lab (47.43 new, verified 2026-10-16)",
     (11,), "Drive"),
    (21, None, 1, "Power supply Mean Well LRS-350-48 (48 V, 7.3 A)", "TRC Electronics", "LRS-350-48",
     "https://www.trcelectronics.com/products/mean-well-lrs-350-48", 36.11, 1, V, (11,), "Drive"),
    # ---- frame
    (22, None, 1, "80/20 20-2020 extrusion, cut to length: 4 x 444 (x-rails), 4 x 710 (posts), 6 x 260 (cross and station rails), "
     "1 x 200 (fork post), 1 x 170 (vial post); $0.0131/mm + $3 per cut", "80/20 Inc", "20-2020", "https://8020.net/20-2020.html",
     round(0.0131 * (4 * 443.7 + 4 * 710 + 6 * 260 + 200 + 170) + 3 * 16, 2), 1, V, (1, 2, 10, 11), "Frame"),
    (23, ("corner_bracket",), 4, "Cast corner bracket for 20 series (posts to cross rails; +4 for the station posts)", "80/20 Inc", "14059",
     "https://8020.net/20-2020.html", 1.31, 1, V, (1, 2), "Frame"),
    (24, None, 70, "M5 drop-in T-nut for 2020 (brackets, side plates, station)", "West3D", "WES5240M5",
     "https://west3d.com/products/roll-in-drop-in-t-nuts-for-2020-extrusions", 0.17, 1, V, (1, 2, 3, 10, 11), "Frame"),
    (25, None, 70, "M5 x 10 button head screw, with blue threadlocker (T-nuts can't take a nylock)", "BelMetric", "M5 x 10 BHCS",
     "https://www.belmetric.com/", 0.12, 1, V, (1, 2, 3, 10, 11), "Frame"),
    (26, None, 1, "Loctite 243 (blue, medium strength) for the T-nut screws; Loctite 222 (purple, low strength) for the thumb screws", "McMaster-Carr",
     "Loctite 243", f"{MC}/loctite/", 27.25, 1, V, (1,), "Frame"),
    (27, ("foot",), None, "Leveling foot, M6 x 40 stud, into an M6 T-nut in the base rail", "TNUTZ", "LF-020-A", "https://www.tnutz.com/product/lf-020-a/",
     1.85, 1, V, (1,), "Frame"),
    (28, ("side_plate_front", "side_plate_back", "motor_plate"), None,
     "6061-T6 1/4 in plate, laser cut from dxf/: two side plates 320 x 345 mm and the 120 mm motor plate (SendCutSend quotes on upload)",
     "SendCutSend", "dxf/*.dxf", "https://sendcutsend.com/", 65.0, 1, "estimate (raw 12 x 24 in plate is $79.38, verified)", (3, 7), "Frame"),
    # ---- gondolas and pivots
    (29, ("gondola",), None, "Gondola, PETG, 313 x 62 x 55 mm, about 90 g (H2D only: 350 x 320 bed)", "printed", "stl/gondola.stl", "", 1.80, 1,
     "filament at $20/kg", (8,), "Printed"),
    (30, ("shoulder_screw",), None, "Shoulder screw, 18-8, 4 mm x 10 mm shoulder, M3 x 5 thread (the gondola pivots)", "McMaster-Carr", "90265A121",
     f"{MC}/90265A121/", 3.14, 1, V, (8,), "Gondolas"),
    (31, ("sleeve_bearing",), None, "Flanged bushing, oil-embedded 841 bronze, 4 ID x 7.02 OD x 6, flange 10 x 1.5 (pressed into the end plates)",
     "McMaster-Carr", "6659K65", f"{MC}/6659K65/", 3.40, 1, V, (8,), "Gondolas"),
    (32, None, 1, "PTFE washer M4, 4.3 x 9 x 0.8, pack of 50 (two per pivot: on the tab and under the head; 48 used)", "McMaster-Carr", "95630A630",
     f"{MC}/95630A630/", 9.99, 1, V, (8,), "Gondolas"),
    (33, None, 1, "M3 nylon-insert locknut, 18-8, pack of 100 (pivots)", "McMaster-Carr", "93625A100", f"{MC}/93625A100/", 6.94, 1, V, (8,), "Gondolas"),
    (34, None, 2, "M5 brass heat-set insert, 5.7 mm long, 6.4 mm hole, pack of 25 (two per gondola, in the hinge lugs)", "McMaster-Carr", "94459A774",
     f"{MC}/94459A774/", 7.27, 1, V, (8,), "Gondolas"),
    (35, ("thumb_screw",), None, "M5 x 16 knurled low-profile thumb screw, 18-8, 11 x 5 mm head: its tip is the module's hinge pin in Sam's 5.3 mm knuckle hole (tool-free swap; Loctite 222)",
     "McMaster-Carr", "92545A179", f"{MC}/92545A179/", 3.18, 1, V, (9,), "Gondolas"),
    (36, None, 13, "Neodymium disc magnet 1/4 x 1/8 in N52 (12 INDEX in the gondola rails + 1 HOME)", "K&J Magnetics", "D42-N52",
     "https://www.kjmagnetics.com/d42-n52-neodymium-disc-magnet", 0.52, 1, V10, (8,), "Gondolas"),
    # ---- modules
    (37, ("sam_mounting_plate",), None, "Mounting plate (Sam's Oct 13 Onshape part), PETG/PLA, about 70 g", "printed",
     "Onshape 581956d5 (Part Studio 1)", "https://cad.onshape.com/documents/581956d5528927957a4c0b98/w/5778b22212c6736ada520515/e/24d73974055f92c0f2fa292f",
     1.40, 1, "filament at $20/kg", (9,), "Modules"),
    (38, ("auger",), None, "Auger (threaded storage, 44T) + cap, lab design (PR #170): from the #134 batch of 16", "lab", "reference/auger-*.step", "",
     0.0, 1, "existing", (9,), "Modules"),
    # ---- station
    (39, ("actuator_body",), None, "Actuonix P16-150-22-12-P linear actuator, 150 mm stroke, potentiometer feedback, 46 mm/s, 50 N, includes #8-32 pins and brackets",
     "Actuonix", "P16-150-22-12-P", "https://www.actuonix.com/p16-p", 90.0, 1, V, (10,), "Station"),
    (55, None, 1, "Shoulder screw 4 x 30 mm, M3 (actuator's rear clevis; cheeks 29.8 mm over) + M3 nylock", "McMaster-Carr", "90265A992",
     f"{MC}/90265A992/", 5.11, 1, V, (10,), "Station"),
    (56, None, 1, "Shoulder screw 4 x 20 mm, M3 (rod end in the yoke; cheeks 19.8 mm over) + M3 nylock", "McMaster-Carr", "90265A124",
     f"{MC}/90265A124/", 5.68, 1, V, (10,), "Station"),
    (40, None, 1, "Actuonix LAC linear actuator control board (closed-loop position from the pot; USB/RC/PWM/0-3.3 V in)", "Actuonix", "LAC",
     "https://www.actuonix.com/lac", 30.0, 1, V, (10,), "Station"),
    (41, None, 1, "12 V supply for the LAC and actuator (Actuonix)", "Actuonix", "12V PSU", "https://www.actuonix.com/lac", 10.0, 1, V, (10,), "Station"),
    (42, ("station_yoke", "fork", "fork_arm", "clevis_bracket", "vial_cup"), None,
     "Station printed parts, PETG: yoke under the electronics carriage, approach fork + arm, base clevis, vial cup", "printed", "stl/", "", 0.60, 1,
     "filament", (10, 11), "Printed"),
    (43, ("sam_electronics_carriage",), None, "Electronics carriage (Sam's Oct 13) with the doser's NEMA 11, 20T pinion and 12 V solenoid", "lab",
     "Onshape 581956d5", "", 0.0, 1, "existing (doser parts)", (10,), "Station"),
    (44, ("load_cell",), None, "Load cell 100 g (TAL221) under the vial", "SparkFun", "SEN-14727", "https://www.sparkfun.com/products/14727", 14.50, 1, V,
     (11,), "Station"),
    (45, None, 1, "HX711 load-cell amplifier", "SparkFun", "SEN-13879", "https://www.sparkfun.com/products/13879", 4.95, 1, V, (11,), "Station"),
    (46, ("vial",), None, "20 mL glass scintillation vial (lab stock; Wheaton 986546 is $383.77 per 500)", "lab / pfstar.com", "986546",
     "https://pfstar.com/986546-20-mL-LS-Vial-22-400-Urea-Cap-PE-Cone-Ln", 0.77, 1, V, (11,), "Station"),
    (47, ("hall",), None, "Hall-effect switch US5881 (unipolar, open drain): INDEX and HOME", "Adafruit", "158", "https://www.adafruit.com/product/158",
     2.00, 1, V10, (11,), "Electronics"),
    # ---- electronics
    (48, None, 1, "Raspberry Pi Zero 2 W (or any spare Pi that runs pigpio)", "Adafruit", "5291", "https://www.adafruit.com/product/5291", 15.00, 1, E,
     (11,), "Electronics"),
    (49, None, 1, "Interface board: 74AHCT125 level shifter (step/dir/enable), pull-ups, screw terminals, perfboard", "Adafruit", "1787",
     "https://www.adafruit.com/product/1787", 6.0, 1, E, (11,), "Electronics"),
    (50, None, 1, "E-stop GCX1136 (22 mm, NC) + enclosure; breaks the 48 V feed to the driver", "AutomationDirect", "GCX1136",
     "https://www.automationdirect.com/pn/GCX1136", 30.0, 1, V10, (11,), "Electronics"),
    (51, None, 1, "IEC C14 inlet with switch + fuse drawer", "Digi-Key", "719W-UEL3BR51",
     "https://www.digikey.com/en/products/detail/qualtek/719W-UEL3BR51/23019206", 7.66, 1, V10, (11,), "Electronics"),
    (52, None, 1, "18 AWG stranded hook-up wire, 25 ft", "Digi-Key", "18UL1007STRBLA25", "https://www.digikey.com/en/products/result?keywords=18UL1007STRBLA25",
     14.57, 1, V10, (11,), "Electronics"),
    # ---- test equipment (not in CAD)
    (53, None, 1, "Digital indicator 0-1 in / 0.01 mm with magnetic base (index repeatability, swing, chain lift)", "Penn Tool Co", "iGaging 35-520",
     "https://www.penntoolco.com/igaging-digital-indicator-universal-arm-magnetic-base-set-35-520", 119.95, 1, V10, (12,), "Test"),
    (54, None, 1, "ADXL343 accelerometer breakout (gondola swing and transit vibration)", "Adafruit", "4097", "https://www.adafruit.com/product/4097",
     5.95, 1, V10, (12,), "Test"),
]


def counts() -> Counter:
    import layout as L
    return Counter(p.key for p in L.placements())


def rows() -> list[dict]:
    c = counts()
    out = []
    for item, keys, qty, desc, vendor, pn, url, price, pack, note, steps, cat in ITEMS:
        q = sum(c[k] for k in keys) + (qty or 0) if keys else qty
        if item == 2:
            q += 2                     # spares
        out.append(dict(item=item, qty=q, desc=desc, vendor=vendor, pn=pn, url=url, unit=price, ext=round(q * price, 2),
                        note=note, steps=steps, cat=cat))
    return out


def totals(rs: list[dict]) -> dict:
    t = sum(r["ext"] for r in rs)
    test = sum(r["ext"] for r in rs if r["cat"] == "Test")
    est = sum(r["ext"] for r in rs if r["note"].startswith("estimate"))
    return dict(total=round(t, 2), without_test=round(t - test, 2), estimated_part=round(est, 2))


def write_csv(rs: list[dict]) -> None:
    with (HERE / "bom.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "qty", "description", "vendor", "part number", "url", "unit USD", "extended USD", "price source", "assembly steps", "category"])
        for r in rs:
            w.writerow([r["item"], r["qty"], r["desc"], r["vendor"], r["pn"], r["url"], f"{r['unit']:.2f}", f"{r['ext']:.2f}", r["note"],
                        " ".join(str(s) for s in r["steps"]), r["cat"]])


if __name__ == "__main__":
    rs = rows()
    write_csv(rs)
    t = totals(rs)
    print(f"{len(rs)} lines; total ${t['total']:.2f}, without test gear ${t['without_test']:.2f}, estimated lines ${t['estimated_part']:.2f}")
