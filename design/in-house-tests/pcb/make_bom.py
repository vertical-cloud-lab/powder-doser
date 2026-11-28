#!/usr/bin/env python3
"""Write bom.csv for FC-1 from fc1_design.PARTS plus DigiKey data.

DigiKey numbers were read from DigiKey product pages on 2026-11-28 between
08:50 and 09:30 UTC (WebFetch of digikey.com; aggregators returned 403/500).
"unverified" marks anything not seen directly.
"""
import csv
import os
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fc1_design as D  # noqa: E402

DK = "https://www.digikey.com/en/products/result?keywords="
SEEN = "DigiKey product page, 2026-11-28"
# MPN: (DigiKey PN, URL, price qty1, price qty10 (each), stock text, alternates)
DIGIKEY = {
    "ADA4530-1ARZ": ("505-ADA4530-1ARZ-ND", "https://www.digikey.com/en/products/detail/analog-devices-inc/ADA4530-1ARZ/5726586",
                     41.95, 34.23, "103 in stock (44 wk lead time)",
                     "none pin-compatible; TI LMP7721MA/NOPB ($9.45, 3425 in stock) needs a board change"),
    "REF3025AIDBZR": ("296-26322-1-ND", "https://www.digikey.com/en/products/detail/texas-instruments/REF3025AIDBZR/1573911",
                      1.55, 1.131, "45,387 in stock", "REF3025EAIDBZR (drop-in, 296-REF3025EAIDBZRCT-ND, 14,160); REF3325AIDBZR"),
    "ADS1115IDGSR": ("296-38849-1-ND", DK + "ADS1115IDGSR", 5.59, 4.265, "29,632 in stock", "ADS1115IDGST ($7.06, 14,013)"),
    "9002-05-01": ("306-1060-ND", DK + "9002-05-01", 7.30, 6.499, "9,313 in stock",
                   "Coto 9002-05-00 (no internal diode; 306-1059-ND, $6.89, 14,703)"),
    "031-5539": ("ARF2045-ND", "https://www.digikey.com/en/products/detail/amphenol-rf/031-5539/252798",
                 8.76, 7.447, "1,059 in stock", "none verified for this footprint (polypropylene insulator)"),
    "MMBT3904LT1G": ("MMBT3904LT1GOSCT-ND", "https://www.digikey.com/en/products/detail/onsemi/MMBT3904LT1G/919601",
                     0.14, 0.086, "2,107,774 in stock", "Diodes MMBT3904-7-F (MMBT3904-FDICT-ND)"),
    "BSS138": ("BSS138CT-ND", "https://www.digikey.com/en/products/detail/onsemi/BSS138/244210",
               0.33, 0.20, "89,266 in stock", "Nexperia BSS138BK,215 (1727-1141-1-ND)"),
    "1N4148W-TP": ("1N4148WTPMSCT-ND", DK + "1N4148W-TP", 0.11, 0.066, "379,285 in stock",
                   "onsemi MMSD4148T1G (MMSD4148T1GOSCT-ND, 342,404); Diodes 1N4148W-7-F is out of stock"),
    "LTST-C171GKT": ("160-1423-1-ND", DK + "LTST-C171GKT", 0.15, 0.104, "73,319 in stock", "LTST-C170GKT (160-1179-1-ND)"),
    "LTST-C171KSKT": ("160-1428-1-ND", DK + "LTST-C171KSKT", 0.17, 0.114, "8,471 in stock", "red LTST-C171KRKT (160-1427-1-ND)"),
    "SM04B-SRSS-TB(LF)(SN)": ("455-SM04B-SRSS-TBCT-ND", DK + "SM04B-SRSS-TB(LF)(SN)", 0.51, 0.433, "190,100 in stock",
                              "none (same part from Adafruit/SparkFun STEMMA/Qwiic boards)"),
    "PREC006SAAN-RC": ("35-PREC006SAAN-RC-ND", DK + "PREC006SAAN-RC", 0.10, 0.078, "17,913 in stock", "any 1x6 2.54 mm header"),
    "PREC002SAAN-RC + SPC02SYAN": ("35-PREC002SAAN-RC-ND + S9001-ND", DK + "PREC002SAAN-RC", 0.20, 0.058,
                                   "46,265 / 1,341,512 in stock", "any 1x2 2.54 mm header and shunt"),
    "CC1206FKNPO9BN103": ("13-CC1206FKNPO9BN103CT-ND", DK + "CC1206FKNPO9BN103", 0.97, 0.61, "3,498 in stock",
                          "KEMET C1206C103F5GACTU (1 %, $7.52); 10 nF polypropylene film (WIMA FKP2) on wires"),
    "C3216C0G1H104J160AA": ("445-7694-1-ND", DK + "C3216C0G1H104J160AA", 0.64, 0.395, "323,320 in stock",
                            "Murata GRM31C5C1H104JA01L (490-6505-1-ND, 19,226)"),
    "GRM2195C1H103JA01D": ("490-1642-1-ND", DK + "GRM2195C1H103JA01D", 0.20, 0.117, "229,133 in stock",
                           "KEMET C0805C103J5GACTU"),
    "CL21B104KBCNNNC": ("1276-1003-1-ND", DK + "CL21B104KBCNNNC", 0.10, 0.045, "3,392,144 in stock", "KEMET C0805C104K5RACTU"),
    "GRM21BR61E106KA73L": ("490-5523-1-ND", DK + "GRM21BR61E106KA73L", 0.17, 0.095, "1,506,900 in stock",
                           "Samsung CL21A106KAYNNNE (out of stock)"),
    "CL21B105KAFNNNE": ("1276-1066-1-ND", DK + "CL21B105KAFNNNE", 0.11, 0.059, "1,675 in stock",
                        "KEMET C0805C105K3RACTU (111,193)"),
    "RC0805FR-0710RL": ("311-10.0CRCT-ND", DK + "RC0805FR-0710RL", 0.13, 0.061, "622,339 in stock", "any 0805 1 %"),
    "RMCF0805FT100R": ("RMCF0805FT100RCT-ND", DK + "RMCF0805FT100R", 0.10, 0.027, "194,268 in stock",
                       "Yageo RC0805FR-07100RL (out of stock until 2026-12-22)"),
    "RC0805FR-071KL": ("311-1.00KCRCT-ND", DK + "RC0805FR-071KL", 0.10, 0.038, "405,037 in stock", "any 0805 1 %"),
    "RC0805FR-071K5L": ("311-1.50KCRCT-ND", DK + "RC0805FR-071K5L", 0.10, 0.038, "426,934 in stock", "any 0805 1 %"),
    "RC0805FR-072K2L": ("311-2.20KCRCT-ND", DK + "RC0805FR-072K2L", 0.10, 0.038, "291,497 in stock", "any 0805 1 %"),
    "RC0805FR-074K7L": ("311-4.70KCRCT-ND", DK + "RC0805FR-074K7L", 0.10, 0.038, "448,873 in stock", "any 0805 1 %"),
    "RC0805FR-0710KL": ("311-10.0KCRCT-ND", DK + "RC0805FR-0710KL", 0.10, 0.038, "1,336,526 in stock", "any 0805 1 %"),
    "RC0805FR-07100KL": ("311-100KCRCT-ND", DK + "RC0805FR-07100KL", 0.10, 0.038, "53,374 in stock", "any 0805 1 %"),
    "RC1206JR-070RL": ("311-0.0ERCT-ND", DK + "RC1206JR-070RL", 0.10, 0.035, "1,109,820 in stock", "wire link"),
    "HVC1206Z1008KET": ("273-HVC1206Z1008KETCT-ND", "https://www.digikey.com/en/products/detail/ohmite/HVC1206Z1008KET/2709632",
                        7.07, 5.532, "7,547 in stock", "none found"),
}

rows = OrderedDict()
for ref, (lib_id, value, fp, pinmap, fields) in D.PARTS.items():
    if ref in D.NOT_IN_BOM:
        continue
    mpn = fields.get("MPN", "")
    key = (mpn, value, fp)
    if key not in rows:
        rows[key] = {"refs": [], "value": value, "footprint": fp, "mfr": fields.get("Manufacturer", ""), "mpn": mpn,
                     "note": fields.get("Note", "")}
    rows[key]["refs"].append(ref)


def refkey(r):
    import re
    m = re.match(r"([A-Z]+)(\d+)", r)
    return (m.group(1), int(m.group(2)))


out = os.path.join(HERE, "bom.csv")
total1 = total10 = 0.0
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ref", "value", "footprint", "qty", "manufacturer", "MPN", "digikey_pn", "digikey_url",
                "unit_usd_qty1", "unit_usd_qty10", "stock_2026-11-28", "how_checked", "alternates", "notes"])
    for key, r in sorted(rows.items(), key=lambda kv: refkey(sorted(kv[1]["refs"], key=refkey)[0])):
        refs = sorted(r["refs"], key=refkey)
        dk = DIGIKEY.get(r["mpn"])
        dnp = any(x in D.DNP for x in refs)
        qty = len(refs)
        note = r["note"]
        if dnp:
            note = (note + "; " if note else "") + "DNP: not fitted, not in the totals"
        if dk:
            pn, url, p1, p10, stock, alt = dk
            if not dnp:
                total1 += p1 * qty
                total10 += p10 * qty
            w.writerow([" ".join(refs), r["value"], r["footprint"], qty, r["mfr"], r["mpn"], pn, url,
                        "%.2f" % p1, "%.3f" % p10, stock, SEEN, alt, note])
        else:
            w.writerow([" ".join(refs), r["value"], r["footprint"], qty, r["mfr"], r["mpn"], "unverified", "",
                        "", "", "unverified", "", "", note])
    # optional / board items
    w.writerow(["(H6)", "PTFE press-fit turret, optional air-wired input", "MountingHole_2.2mm_M2 (2.2 mm hole)", 1,
                "Keystone", "11301", "36-11301-ND", "https://www.digikey.com/en/products/detail/keystone-electronics/11301/2170335",
                "2.09", "1.581", "377 in stock", SEEN, "Keystone 11218 feed-through (1.7 mm hole, does not fit H6)",
                "optional; hole 0.086 in per Keystone datasheet M65p140"])
    w.writerow(["PCB", "FC-1 v1.0 bare board, 2 layers, 1.6 mm, 50 x 40 mm", "fc1-gerbers.zip", 1, "JLCPCB or OSH Park", "",
                "", "https://jlcpcb.com/", "", "", "n/a", "see README (fab prices not verified with a live quote)", "", ""])
    w.writerow(["TOTAL (fitted parts, excl. PCB, DNP and optional)", "", "", "", "", "", "", "",
                "%.2f" % total1, "%.2f" % total10, "", "", "", "qty10 column = per-board cost when buying 10 of each"])
print("wrote bom.csv; per-board parts cost: $%.2f (qty 1 prices), $%.2f (qty 10 prices)" % (total1, total10))
