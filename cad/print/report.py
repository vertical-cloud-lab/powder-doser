"""Write README.md from slice_report.json and audit.json of every design (run after slice.py and previews.py).
paternoster and chain-carousel-v2 share the Plates and audit sections; chain-carousel-v11 (PR #185) has its own section."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESIGNS = ("paternoster", "chain-carousel-v2")
INSERT = "heat-set insert"

# What the mesh numbers and Studio's warnings don't say: holes, inserts, fit, open points. Shared parts are the same
# builder in both designs (the station came over from v2), so their notes are too.
COMMON = {
    "uyoke_base": "The lead's P16 version (9.3 x 3.1 counterbore, 9.3 x 6.3 x 7.2 slot, 3.96 mm press hole for the 4 x 38 dowel). "
                  "Upside down (crossbar's top face on the bed): counterbore and slot open upward. The 30 mm tongue overhangs the "
                  "20 mm crossbar by 5 mm each side at the top: two 5 x 6 mm flat ledges, which Studio prints without a warning "
                  "(not a mating face). Dowel hole and the two 4.0 mm arm holes horizontal; ream the dowel hole if the press is too hard.",
    "yoke_stop": "6 x 4 x 1.3 mm: only 24 mm2 on the bed, hence the station plate's 3 mm brim (Studio's auto brim adds none). "
                 "Bonded to the steel arm.",
    "yoke_stop_m": "As yoke_stop (mirror image).",
    "pin_boss": "1.5 mm plate flat on the bed. The 4.0 mm hole takes a pressed 4 mm steel pin: printed holes come out "
                "0.1-0.2 mm small, so ream to 4.0 if the press is too hard.",
    "pin_boss_m": "As pin_boss (mirror image).",
    "magnet_bracket": "As drawn; magnet cup opens upward. The M2.5 clearance holes (2.8 mm) in the 3 mm foot are horizontal.",
    "fork": "Slot and lead-in vertical: no overhangs. No fastener holes are modelled (to the fork arm / post).",
    "clevis_bracket": "The lead's P16 version (CLEVIS_GAP 8.4, R4 cheeks, web). Foot on the bed; 3.7 mm cheeks, 4.15 mm pin hole "
                      "horizontal with 1.9 mm of wall (ream to 4.2 for the 4 mm shoulder screw); two 5.5 mm foot holes vertical.",
    "vial_cup": "As drawn: cup and arm on the bed, no overhangs.",
    "vial_funnel": "Mouth on the bed: the 1.6 mm cone wall (3-4 lines) leans in 24 deg from vertical, so no support.",
    "sam_mounting_plate": "Sam's Onshape part plus our cuts, underside on the bed: the two M3 " + INSERT + " holes (4.0 mm, 4.0/4.5 mm "
                          "deep) open to the bed with 2.8 mm of wall round them and 6.4 mm of plate above; the 4.2 mm locating-pin "
                          "hole and 4.2 x 6 slot also open to the bed. Hinge knuckle holes horizontal.",
}
NOTES = {
    "paternoster": {
        "gondola": "As it hangs. 312.3 mm long: fits the left nozzle's 325 mm with 6 mm to spare each side, 4 per plate "
                   "(4118 mm2 on the bed each, no brim needed). CHANGED: the saddle's V cheeks started 8 mm up in mid-air "
                   "(Studio: floating regions); now they stand on the bar. Remaining unsupported areas are bridges: floor strips "
                   "between rib and rail, the INDEX magnet pocket's roof (open to the bed), the 7.0 mm bushing bores and the 6.4 mm "
                   "M5 " + INSERT + " holes in the hinge lugs (horizontal; 3.8 mm of wall round the inserts).",
        "fork_arm": "Plain 20 x 5.5 x 12 block (layout._fork_arm), flat. No fastener holes are modelled.",
        "hold_bracket": "Plain 28 x 12 x 9 block (parts.hold_down_bracket). No holes are modelled for the M4 screws the UHMW strip "
                        "is drilled for, or for the side plate.",
    },
    "chain-carousel-v2": {
        "carriage": "Plate's outer face on the bed (11 900 mm2 first layer), on the H2D bed's diagonal: 351 x 60 mm needs "
                    "(351 + 60) / sqrt 2 = 291 mm in each direction of the left nozzle's 325 x 320 area. One per plate. "
                    "CHANGED (print file only): the two tab-hook fingers were 9.2 mm cantilevers over the 1.55 mm tab slot "
                    "(Studio: floating cantilever); the print file has a 0.8 mm break-off web across each slot's mouth that "
                    "makes them bridges. Cut both webs off flush before fitting the carriage to the tabs. Remaining: "
                    "5.15 mm hinge-pin holes horizontal, 0.8 mm snap-hook lips (35 deg), counterbores open to the bed.",
        "hold_down": "Side-plate face on the bed: foot, web and lip stack with no overhang; M5 " + INSERT + " holes (6.4 mm) open to "
                     "the bed with 4.8 mm of wall. The hall switch looks through a 0.8 mm window on purpose (prints as two thin lines).",
        "tensioner_block": "Back face on the bed: M5 screw holes and the locknut slot vertical, the 5.5 mm jack-screw hole horizontal.",
        "level_wedge": "40 x 40 x 6 block as modelled, flat.",
        "fork_arm": "Was 20 x 0.5 x 12 mm (under two line widths: the fork's side face sat 0.5 mm from the post); the lead "
                    "redrew it (layout._fork_arm) as a 20 x 29.5 x 6 mm plate on the post's top: printed flat, 6.6 mm M6 "
                    "clearance hole, two 4.0 mm insert holes with 2.5 mm of wall.",
        "vial_cup": "The lead's version with the 63 mm arm for the 47 mm TAL221 (95 mm long overall). As drawn, no overhangs.",
    },
}


V11 = "chain-carousel-v11"
NOTES_V11 = {
    "carriage": "Since v10 neither face is flat: the hinge lugs (21 mm), the ribs (7 mm) and the latch housing stand on the outer face, "
                "the two tab hooks (6.55 mm) on the inner face. Inner face down, only the hooks' fingers touch the bed (156 mm2) and the "
                "plate's 9300 mm2 are 6.55 mm up: Studio, supports off: \"floating cantilever\". So it prints on tree supports from the "
                "build plate (none inside the 1.55 mm tab slots, which stand on the fingers): 77.6 g with them, 56.5 g without, about "
                "21 g of support each. Outer face down would be worse (the plate 21 mm up on the lugs' rounded ends). On the H2D bed's "
                "diagonal: the 391 x 66 mm outline is 305 x 301 mm at 44.6 deg (the 40 mm tongues cut its corners), inside the left "
                "nozzle's 325 x 320 with about 10 mm to spare each side (toolpaths x 6-317, y 6-313). The file keeps the break-off webs "
                "across the tab slots' mouths (`print_web=True`, as v11's own stl/): cut them off flush. The support comes off the inner "
                "face, which seats on the A-1 tabs: sand any nubs flat.",
    "sam_mounting_plate": "Sam's plate with v11's additions (`parts11.plate_additions_v11`: carried on to the cap's end with clip 2, the cap "
                          "saddle and the latch keeper, the door housing's inserts, the T-bracket's two M3 " + INSERT + " holes; no motor "
                          "relief; since 2026-11-27 the door housing's M2 inserts at |y| 14.35 and the channel wall cut back to |y| 16.3 "
                          "beside its arms), 257 mm long. Underside on the bed (10 959 mm2), no floating regions; 380 mm2 of "
                          "bridges and hole roofs. "
                          "Five per H2D plate (5 x 54 mm plus gaps: 302 of the 320 mm); all 13 are printed (BoM item 39).",
    "t_bracket": "One solid since v11's fix (item 3). On its side: the T's profile on the bed (104 mm2), 16 mm tall, so the head's "
                 "underside, which rides on the rail's lips, is a wall, and the head pulls along the layers, not across them. The two M3 "
                 "clearance holes (3.4 mm, 6 mm counterbores) are horizontal.",
    "door_housing": "One solid since v11's fix (item 2). As drawn: the cap's top face on the bed (115 mm2), rails and spring tower up; "
                    "the two mounting arms leave the rails 6.5 mm up as 22 mm cantilevers (Studio, supports off: floating cantilever), so the "
                    "housings print on tree supports under the arms. The shutter's grooves and the tower's channel open upward, so "
                    "nothing grows inside them.",
    "door_shutter": "Flat, no overhang. No hole is modelled for the 1.5 mm door rod, which the BoM says is pressed in (item 5, still open).",
    "door_head11": "6 x 6 x 2.5 mm, flat, the rod's 1.5 mm hole vertical (printed holes run 0.1-0.2 mm small: a press fit, then glue "
                   "as the BoM says). Only 34 mm2 on the bed: the module_parts plate's 3 mm brim holds it.",
    "latch_bolt": "The carrier and its rest shelf with the dowel's 4.0 mm hole, 2 mm deep (item 4: the builder fuses the dowel for the "
                  "assembly; v11's build.py and `print_variants.latch_bolt` export this carrier). On its back face (97 mm2): the hole "
                  "opens upward and prints round (press the dowel in; ream to 4.0 if too tight), the shelf is a 2 mm fin, the follower's "
                  "3.0 mm hole is horizontal, and the faces that slide in the latch housing are walls.",
    "ec11": "One solid since v11's fix (item 1). On its -y side: the motor cheek and the side bar on the bed (1595 mm2), so the "
            "rail's T-slot, the door ramp's lips and the P16's pin hole run vertical and the faces the T-brackets, door heads and pin "
            "ride on are walls, not supported ceilings. The door ramp's end and the solenoid collar start in mid-air, 5.5 and 8.7 mm over "
            "the bed (Studio, supports off: floating cantilever): tree supports from the build plate, none inside the T-slot. The motor plate's 22.4 mm hole "
            "lies on its side (its top arches over).",
    "pillar11": "212 mm tall: H2D only (the A1 mini stops at 180). Its wall is two 0.42 mm lines since v11's fix (item 6: 0.85 mm, "
                "was 1.6). The deck under the beaker's socket bridges the tube's bore (1222 mm2 unsupported); Studio prints it "
                "without a warning.",
    "p16_bracket11": "The flange's bar face on the bed (752 mm2), the cheeks up: the 4.15 mm pin hole (for the 4 mm shoulder screw; "
                     "ream to 4.2) horizontal through the R6 bosses, the two 5.5 mm M5 holes vertical.",
    "guide11": "Rebuilt from the EC's moved shoe (item 1): its seat now behind the arm. On its side: its L-shaped profile (flange, "
               "plate, seat block) on the bed (724 mm2), 22 mm tall; the seat's 90 deg cone and 45 deg funnel mouth lie on their "
               "side (45 deg walls, no support), the flange's two 5.5 mm M5 holes horizontal. Standing as drawn it would be 111 mm "
               "tall with 393 mm2 overhanging.",
    "latch_rail11": "On its side: the cam's and the foot's +y ends on the bed (390 mm2), 57 mm tall. The cam's flat and 30 deg ramps, "
                    "which the follower rides, print as walls (0.2 mm steps along the ramps); the web and foot stand on the cam; the "
                    "foot's two M5 holes horizontal. As drawn, the web and foot would hang 1650 mm2 over the bed.",
    "hold_down": NOTES["chain-carousel-v2"]["hold_down"],
    "tensioner_block": NOTES["chain-carousel-v2"]["tensioner_block"],
    "side_tab": "As drawn: the side-plate face on the bed (564 mm2); lip, foot and web stand on it with no overhang; the two 5.5 mm "
                "clearance holes and their 9.2 mm counterbores vertical.",
    "side_tab_m": "As side_tab (mirror image).",
    "catch": "The 24 x 10 x 3 mm tab on the bed (223 mm2), the 10 mm spacer up; the M4 hole (4.2 mm) vertical.",
    "hatch_knob": "Cut out of `parts3.hatch_door`, which draws the knob as part of the acrylic door: a 16 x 14 mm cylinder with a "
                  "10 x 4 mm cap, its bonded face on the bed (201 mm2).",
}


# v11: the parts that aren't printable as drawn, and what to change in v11's CAD (checked by building the changed solids here, without
# editing cad/chain-carousel-v11/)
V11_FIXES = [
    "### What the slicing found in v11's CAD, and what was changed\n",
    "Found by splitting each exported mesh into its connected bodies, measuring the gaps in the CAD (OCC distances) and slicing each "
    "part alone; the proposed fixes were built from v11's own functions in a scratch copy and checked for one solid and for overlaps "
    "with the parts round them. Items 1-4 and 6 were then made in v11's CAD on 2026-11-27, and everything above is re-exported and "
    "re-sliced from it; item 5 is still open.\n",
    "1. **EC v11** (`parts11.ec_v11`, `params.py`), **fixed in v11.** It was five separate solids: the front (door ramp walls and roof, "
    "spine, solenoid collar, rail block: 17 860 mm3), the back (motor plate, cheeks, strap, arm, the P16's clevis: 25 869 mm3), the door "
    "ramp's two lips (393 mm3 each) and the guide shoe (490 mm3). The lips stopped 0.05 mm short of the channel's walls; the spine ran "
    "to x 93.5 and ended inside the motor plate's 22.4 mm hole, 1.6 mm from its edge, after running through the 24T pinion (652 mm3 at "
    "rest) and the NEMA 11's shaft; the shoe hung 1.0 mm off the arm (v11 had moved the arm to z -30 to -20 and left v10's shoe at "
    "-38 to -31), and `guide11`, built from its tip, put its seat block inside the arm (1759 mm3). `check_interference.py` skipped all "
    "three pairs (\"ec11\" with \"pinion24\", \"nema11\" and \"guide11\"). Now: `DOOR11_LIP_W` 2.2 -> 2.3; the spine stops at "
    "x 71.5, widens to |y| 19.5 over x 69.5-71.5, and two 4 x 4.5 mm bars at |y| 15.5-19.5 run beside the pinion to the cheeks "
    "(x 69.5-89.91); the shoe sits behind the arm (`SHOE11` = (133, 145, -24.5, -31.6), `SHOE11_Y` 36) on a bracket "
    "(`SHOE11_BRACKET`) with a riser onto the arm's far face, its nose a true 90 deg cone, and `guide11` follows its tip. One solid "
    "(45 068 mm3); EC-pinion 0, EC-guide 0, EC-NEMA 11 4.3 mm3 (the face it is bolted to). It still needs supports in every "
    "orientation; on its side, as printed here, two regions start in mid-air (the door ramp's end and the "
    "solenoid collar) and 2710 mm2 is unsupported.\n",
    "2. **Door housing** (`parts4.door_housing_v4`, which `parts10.door_housing_v10` and v11 reuse), **fixed in v11.** It was five "
    "solids: the mounting arms (|y| 12.8-14.6) stood 0.3 mm off the rails (|y| <= 12.5), and each arm's 2.2 mm M2 hole (at |y| 13.7) "
    "was wider than the 1.8 mm arm, so it cut the arm in two. Now the arms run |y| 12.45-16.25 with the M2 holes at |y| 14.35 "
    "(`DOOR_M2_Y11`, 0.8 mm of wall each side); the mounting plate's M2 inserts moved to |y| 14.35 (`parts10.plate_additions_v10`) and "
    "its channel wall is cut back to |y| 16.3 over x 4.8-22 (`parts11.plate_additions_v11`). One solid (2161 mm3), clear of the plate. "
    "The arms are 22 mm cantilevers off the rails, so in every orientation something needs support; as drawn it is the arms' "
    "undersides, 6.5 mm up, and the housings print on tree supports.\n",
    "3. **T-bracket** (`parts11.t_bracket_v11`), **fixed in v11.** Its stem started at `zu + 0.01` (z -23.99) and the head ended at "
    "`zu` (-24.00): the head was a separate solid 0.01 mm off the stem. Now `zu - 0.01`: one solid, and the print file is the CAD's "
    "part again (the earlier print variant is gone).\n",
    "4. **Latch bolt** (`parts7.latch_bolt_v7`), **fixed in v11's `build.py`.** The builder returns the steel dowel fused to the printed "
    "carrier (`pin.union(blk)`, which the assembly wants), and `build.py` exported that as `stl/latch_bolt.stl`, so the dowel would have "
    "been printed in PETG with no hole for the real one. `build.py` now exports the carrier with the dowel's 4.0 mm hole, 2 mm deep; "
    "these files use the same carrier (`print_variants.latch_bolt`).\n",
    "5. **Door shutter and rod** (`parts10.door_shutter_v10`, `parts11.door_rod_v11`), **still open: not fixed.** The shutter prints "
    "fine but can't take its rod. The 1.5 mm rod is \"pressed into each shutter's boss\" (BoM item 116), but no hole is modelled: the "
    "rod is drawn 1 mm into the shutter (z -5 to -4), and its axis (the spring's, x -2.85) is 0.35 mm inside the face of the 1.8 mm "
    "boss (x -3.2 to -1.4), which can't grow past the housing tower's channel (x -3.3). A 1.5 mm hole there breaks 0.4 mm out of the "
    "boss. Pressing the rod in needs a hole about 3 mm deep (`DOOR11_ROD_Z0` -4 -> -2) with 0.8 mm of boss round it, i.e. the boss "
    "3.1 mm across on the rod's axis, so the tower's channel, the spring's axis and the cap's 1.8 mm hole have to be laid out again "
    "round it. (The rod also runs 0.3 mm into the tower's wall along its length, 2.6 mm3; the check skips (\"door_rod11\", "
    "\"door_housing\").)\n",
    "6. **Beaker pillar** (`params.PILLAR11`), **fixed in v11.** Its 1.6 mm wall (3-4 lines) sliced to 53.6 g, not the BoM's \"near "
    "30 g\" (item 117: \"vase-mode walls (two 0.4 mm lines)\"), and spiral vase mode can't print it: the deck and the beaker's socket "
    "need top layers, which vase mode doesn't print. Now `PILLAR11` = (40.0, 0.85), two 0.42 mm lines printed normally: "
    "29.9 g, 3 h 47 min sliced.\n",
    "7. **Carriage** (not a defect; unchanged): it prints, but only on supports, about 21 g and 1 h 37 min more per carriage "
    "(13 times). Printing it flat with no support would need a flat inner face, e.g. the two tab hooks made as separate printed clips "
    "held by the tab's M3 screw, which changes how the carriage slides onto the tabs; not proposed here.\n",
]


def hm(s: int | None) -> str:
    if not s:
        return "-"
    h, m = divmod(round(s / 60), 60)
    return f"{h} h {m:02d} min" if h else f"{m} min"


def orient_txt(spec) -> str:
    return "as drawn" if not spec else ", ".join(f"{d:+d} deg about {a}" for a, d in spec)


def h2d_left_nozzle_only(r: dict) -> bool:
    """Every H2D plate uses filament 1 only, on one 0.4 mm nozzle, with no prime tower or wipe (from slice_report.json)."""
    h2d = [p for p in r["plates"] if p["printer_key"] == "h2d"]
    return all([f["id"] for f in p.get("filaments_used", [])] == ["1"] and len(p.get("nozzles", [])) == 1
               and all(float(n["diameter"]) == 0.4 for n in p.get("nozzles", [])) and not p.get("prime_tower_in_gcode") for p in h2d)


def plate_table(w, r: dict, design: str) -> None:
    """A design's plates table (one row per distinct plate, how many prints of it) and the totals line."""
    w("### Plates\n")
    w("| Plate | Printer | Parts (quantity) | Prints | Time (each) | PETG (each) | Layers | Support | Files |\n|---|---|---|---|---|---|---|---|---|")
    tot = {}
    for p in r["plates"]:
        parts = ", ".join(f"{k} x{v}" for k, v in p["parts"].items())
        files = " ".join(f"[{lbl}]({design}/{p[k]})" for k, lbl in (("gcode_3mf", "3mf"), ("studio_png", "Studio"), ("toolpath_png", "toolpaths")) if p.get(k))
        name = f"{p['plate']} (NOT PRINTABLE AS DRAWN)" if p.get("blocked") else p["plate"]
        sup = "tree, build plate only" if p.get("support_used") else ("off, 3 mm brim" if p.get("brim_mm") else "off")
        w(f"| {name} | {p['printer']} | {parts} | {p.get('copies', 1)} | {hm(p.get('print_time_s'))} | {p.get('filament_g')} g | "
          f"{p.get('layers')} | {sup} | {files} |")
        key = ("blocked" if p.get("blocked") else "ready", p["printer"])
        t = tot.setdefault(key, [0, 0, 0.0])
        c = p.get("copies", 1)
        t[0] += c
        t[1] += (p.get("print_time_s") or 0) * c
        t[2] += (p.get("filament_g") or 0) * c
    w("")

    def line(keys):
        n = sum(tot[k][0] for k in keys)
        return n, sum(tot[k][1] for k in keys), sum(tot[k][2] for k in keys)
    ready = [k for k in tot if k[0] == "ready"]
    blocked = [k for k in tot if k[0] == "blocked"]
    parts_txt = "; ".join(f"{k[1]}: {v[0]} prints, {hm(v[1])}, {v[2]:.0f} g" for k, v in tot.items() if k[0] == "ready")
    n, t, g = line(ready)
    if blocked:
        w(f"Totals, Studio's estimates. Ready to print: {parts_txt}; together {n} prints, {t / 3600:.1f} h of printing, {g:.0f} g of PETG. "
          + "Not printable as drawn: " + "; ".join(f"{k[1]}: {hm(v[1])}, {v[2]:.0f} g" for k, v in tot.items() if k[0] == "blocked")
          + f". All: {r['total_print_time_h']} h, {r['total_filament_g']:.0f} g.\n")
    else:
        w(f"Totals, Studio's estimates: {parts_txt}; together {n} prints, {t / 3600:.1f} h of printing, {g:.0f} g of PETG.\n")


def v11_section(w) -> None:
    """chain-carousel-v11 (PR #185): its plates, the per-part audit and the parts that are not printable as drawn."""
    r = json.loads((HERE / V11 / "slice_report.json").read_text())
    a = json.loads((HERE / V11 / "audit.json").read_text())
    w("## chain-carousel-v11 (PR #185)\n")
    w("Every printed part of [`cad/chain-carousel-v11/`](../chain-carousel-v11/) (its `bom.py`'s \"Printed\" lines: items 36-39, 77, 83, "
      "86, 93, 106 and 117), exported from v11's own builders by `export_printed.py`: the same solids as v11's `stl/`, volume for volume (the carriage with "
      "its break-off webs and the latch bolt's carrier as v11's `build.py` exports them, built here by "
      "[`chain-carousel-v11/print_variants.py`](chain-carousel-v11/print_variants.py)), plus the side hatch's knob, which v11 draws as "
      "part of the acrylic door. They are oriented, laid out and sliced with the settings above. Quantities are v11's `layout.placements()` counts: 13 of every module part and all 13 "
      "mounting plates (BoM item 39: \"Print all 13\"). Identical plates are sliced once and printed as many times as the Prints column "
      "says.\n")
    w("![v11 plates](chain-carousel-v11/plates.png)\n")
    blocked_plates = [p["plate"] for p in r["plates"] if p.get("blocked")]
    if blocked_plates:
        w("**Not printable as drawn:** " + ", ".join(blocked_plates) + " (see below). Their plates are sliced as drawn only for the time "
          "and weight: don't print them until the CAD is fixed.\n")
    else:
        w("**Status, 2026-11-27:** the first slicing of v11 found the electronics carriage (EC v11) and the outlet door housing in "
          "pieces, the T-bracket's head off its stem, the steel dowel printed as part of the latch carrier and the pillar twice the "
          "BoM's weight. All of these were fixed in v11's CAD the same day (items 1-4 and 6 below) and everything here is re-exported "
          "and re-sliced from the fixed CAD: every part is one solid and every plate is ready to print. Still open: the door shutter "
          "has no hole for its rod (item 5).\n")
    plate_table(w, r, V11)
    ok = h2d_left_nozzle_only(r)
    w("The carriage, EC and door-housing plates have tree supports (Studio 2.08 turns `tree(auto)` into organic trees), from the build "
      "plate only. "
      "The two A1 mini plates of small parts get the 3 mm outer brim (door heads: 34 mm2 on the bed each). "
      + ("Every H2D file uses filament 1 only, on one 0.4 mm nozzle (extruder 1, the left: `filament_map` 1,2), with no prime tower or "
         "wipe on the other nozzle (`filaments_used`, `nozzles` and `prime_tower_in_gcode` in [slice_report.json](chain-carousel-v11/slice_report.json), "
         "read from each file's slice_info.config and G-code)." if ok else
         "CHECK: an H2D file uses more than filament 1 on one 0.4 mm nozzle, or has a prime tower: see slice_report.json.")
      + " The carriage goes on the H2D bed's diagonal, one per plate.\n")
    w("### Printability audit\n")
    w("As for the other designs: `audit.py` on the mesh in print orientation, and each part sliced alone with supports off.\n")
    w("| Part | Qty | Orientation | On the bed (mm) | First layer | Overhang > 50 deg | Floating islands | Thin layers | Studio, supports off | Alone | Notes |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for k, v in a.items():
        m, s_ = v["mesh"], v["studio_supports_off"]
        warn = "; ".join(s_.get("slicer_warnings") or []) or "no warnings"
        sz = " x ".join(f"{x:g}" for x in m["size_mm"])
        w(f"| {k} | {v['qty']} | {v['why'] if v['why'].startswith('as ') else orient_txt(v['orientation']) + ': ' + v['why']} | {sz} | "
          f"{m.get('first_layer_mm2', '-')} mm2 | {m['overhang_area_mm2']} mm2 | {m.get('n_floating_islands', '-')} | "
          f"{m.get('thin_wall_layers', '-')} | {warn} | {s_.get('print_time')}, {s_.get('filament_g')} g | {NOTES_V11.get(k, '')} |")
    w("")
    w("Thin layers: the carriage's are its 0.8 mm break-off webs, the hold-down's its 0.8 mm hall window (both on purpose).\n")
    for t_ in V11_FIXES:
        w(t_)



V12 = "chain-carousel-v12"
NOTES_V12 = {
    "ec12": "EC v12 (`parts12.ec_v12`): v11's front half; behind the pinion the cradle's pivot bosses, an outer -y rail and a cross "
        "bar, the roof over the spring with its up-stop pad, the magnet's post, the slot for the P16's rod-end tab and the second "
        "guide shoe on the -y side. One solid (48 063 mm3; EC v11 45 068). EC v11 printed on its -y side, where EC v12 has only "
        "the second shoe and its bracket (125 mm2 on the bed), so EC v12 prints on its +y side, on the arm's outer face (312 "
        "mm2): the rail's T-slot, the door ramp's lips and the P16's pin hole stay vertical. Sliced alone on tree supports either "
        "way: 3 h 08 min and 56.8 g both, with less of Studio's automatic brim on the arm. As in v11, the door ramp's end and the "
        "solenoid collar start in mid-air (supports off: floating cantilever), so it prints on tree supports.",
    "cradle12": "The pinion cradle (`parts12.cradle_v12`), one per rig, one solid (9586 mm3 since the fix in item 1 below). On the motor "
        "plate's front face (646 mm2): the motor's 22.4 mm bore, the four M2.5 holes and both dowel bores vertical, so they print "
        "round; the pivot tube, top bar, cheeks and lug stand up off the plate; the lug's M3 insert hole and the spring's peg "
        "horizontal. Every other axis orientation has floating regions or over 700 mm2 of overhang. Clean with supports off since "
        "the fix; it prints with the EC, on that plate.",
    "guide12": "The second guide (`parts12.guide_hanger_v12`): guide11's hanger for the second beam, on the loop's other side; one per "
        "rig, one solid (13 756 mm3). On its side like guide11: its L-shaped profile on the bed (671 mm2), 22 mm tall; the seat's "
        "cone and funnel mouth on their side (45 deg walls), the flange's two M5 holes horizontal. Clean with supports off. It "
        "goes on the EC's plate because the A1 mini's station plate has no room left beside guide11.",
    "door_housing": "v12's housing (`parts12.door_housing_v12`): the spring's tower bored out (3.6 mm) and carried 0.85 mm forward; one solid "
        "(2189 mm3). As v11's: the cap's top face on the bed (119 mm2), the bore vertical; the mounting arms are 22 mm "
        "cantilevers 6.5 mm up (supports off: floating cantilever, as v11's), so the housings print on tree supports.",
    "door_shutter": "v12's shutter (`parts12.door_shutter_v12`): a round 3.2 mm boss with the rod's 1.55 mm hole (a press fit for the 1/16 in "
        "rod), which closes v11's item 5; one solid (187 mm3). Flat as v11's (117 mm2), the boss on top and its hole horizontal; "
        "clean. Thin layers: the boss's 0.83 mm wall round the hole.",
}
V12_CHANGES = ("* **EC v12** replaces EC v11; it prints on its +y side, not v11's -y side (see the audit), on the same H2D plate with tree "
    "supports, which now also carries the cradle and the second guide.\n"
    "* **The pinion cradle** (new) prints with the EC. Its first slice found a floating cantilever and a weak top bar, fixed in "
    "the CAD the same day (below); it now slices clean on its own.\n"
    "* **The second guide** (new) prints with the EC too: the A1 mini's station plate (v11's, unchanged) has no room for it.\n"
    "* **The door housing and shutter** are v12's (the bored tower; the round boss with the rod's hole, v11's item 5) in v11's "
    "orientations and plates.\n"
    "* Everything else, and the carriage, mounting-plate, pillar and station plates, is v11's.\n")
V12_FINDINGS = [
    "### What the slicing found in v12's CAD, and what was changed\n",
    "1. **Pinion cradle** (`parts12.cradle_v12`, `params.CRADLE12_TOP`), **fixed in v12.** The first slice (supports off) warned \"floating cantilever\". The cause was the block at the top bar's far end (`_box(tx1 - 4.0, tx1, -16.0, -14.3, zf, PZ + 3.5)`: x 124-128, y -16 to -14.3, z -51.5 to -30.5 in Sam's frame), meant to join the bar to the tube: the bar was only |y| <= 9 wide, so the block missed it by 5.3 mm and hung 14 mm off the tube (printed plate-down: 34.1 mm up, 29 mm2 over nothing, up to 7 mm from anything below; a scratch copy without it sliced clean). The same gap kept both cheeks off the bar, so the bar (the spring's seat 22.5 mm out) hung on a 0.7 x 18 mm strip of the plate (the plate stopped at z -49); the +y cheek was 0.31 mm thick, under one line; and two M2.5 counterbores broke out of the plate's edges. Now the bar is |y| <= 16 and meets both cheeks and the block (which becomes a bridge), the plate runs from the bar's far face (z -51.5) to z -20.0 and out to y 14.5, the +y cheek is 1.7 mm (y 14.3-16.0), and only the two lower M2.5 heads are counterbored (r 2.3, 1.5 mm deep). Re-exported and re-sliced: one solid (9586 mm3, was 7705), no floating regions or thin layers, 102 mm2 of overhang (was 169), and clean with supports off (1 h 08 min, 9.9 g).\n",
]


def v12_section(w) -> None:
    """chain-carousel-v12 (PR #185): its plates, what changed from v11, and the audit of the parts that differ from v11's."""
    r = json.loads((HERE / V12 / "slice_report.json").read_text())
    a = json.loads((HERE / V12 / "audit.json").read_text())
    new = [k for k, v in a.items() if not v.get("audit_from")]
    same = [k for k in a if k not in new]
    w("## chain-carousel-v12 (PR #185)\n")
    w("Every printed part of [`cad/chain-carousel-v12/`](../chain-carousel-v12/) (its `build.py`'s printed parts, Sam's mounting plate "
      "and the side hatch's knob), exported from v12's own builders by `export_printed.py` (with "
      "[`chain-carousel-v12/print_variants.py`](chain-carousel-v12/print_variants.py), v11's three print variants) and sliced with the "
      "settings above; quantities are v12's `layout.placements()` counts, as v11's. v12 is v11 with the spring-loaded pinion: EC v12 "
      "(`ec12`) replaces EC v11, and the pinion cradle (`cradle12`) and the second guide hanger (`guide12`) are new, one of each per rig. "
      f"v12 also bores the door housing's spring tower and gives the shutter a round boss with the rod's hole (v11's item 5). The other "
      f"{len(same)} parts export byte-identical to v11's STLs and print in v11's orientations, so their audit is v11's above "
      "(`slice.py --reuse-audit chain-carousel-v11`); every plate is sliced again.\n")
    w("![v12 plates](chain-carousel-v12/plates.png)\n")
    plate_table(w, r, V12)
    w("The carriage, EC and door-housing plates have tree supports from the build plate only, as v11's; the cradle and the second guide "
      "print with the EC. The two A1 mini plates of small parts get the 3 mm outer brim. "
      + ("Every H2D file uses filament 1 only, on one 0.4 mm nozzle (extruder 1, the left: `filament_map` 1,2), with no prime tower or "
         "wipe on the other nozzle ([slice_report.json](chain-carousel-v12/slice_report.json))." if h2d_left_nozzle_only(r) else
         "CHECK: an H2D file uses more than filament 1 on one 0.4 mm nozzle, or has a prime tower: see slice_report.json.") + "\n")
    w("### What changed from v11\n")
    w(V12_CHANGES)
    w("### Printability audit\n")
    w(f"The parts whose files differ from v11's ({', '.join(new)}), as for the other designs: `audit.py` on the mesh in print orientation, "
      "and each part sliced alone with supports off.\n")
    w("| Part | Qty | Orientation | On the bed (mm) | First layer | Overhang > 50 deg | Floating islands | Thin layers | Studio, supports off | Alone | Notes |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for k in new:
        v = a[k]
        m, s_ = v["mesh"], v["studio_supports_off"]
        warn = "; ".join(s_.get("slicer_warnings") or []) or "no warnings"
        sz = " x ".join(f"{x:g}" for x in m["size_mm"])
        w(f"| {k} | {v['qty']} | {v['why'] if v['why'].startswith('as ') else orient_txt(v['orientation']) + ': ' + v['why']} | {sz} | "
          f"{m.get('first_layer_mm2', '-')} mm2 | {m['overhang_area_mm2']} mm2 | {m.get('n_floating_islands', '-')} | "
          f"{m.get('thin_wall_layers', '-')} | {warn} | {s_.get('print_time')}, {s_.get('filament_g')} g | {NOTES_V12.get(k, '')} |")
    w("")
    for t_ in V12_FINDINGS:
        w(t_)


def main() -> None:
    reps = {d: json.loads((HERE / d / "slice_report.json").read_text()) for d in DESIGNS}
    audits = {d: json.loads((HERE / d / "audit.json").read_text()) for d in DESIGNS}
    r0 = reps[DESIGNS[0]]
    L = []
    w = L.append
    w("# Print files for the printed parts of both carousels (Bambu Studio)\n")
    w("Every 3D-printed part of [`cad/paternoster/`](../paternoster/) and [`cad/chain-carousel-v2/`](../chain-carousel-v2/), "
      "plus Sam's mounting plate (printed for the extra modules in both), oriented, laid out on plates and sliced with Bambu "
      "Studio's own CLI. Quantities are the BoMs' (counted from each design's `layout.placements()`).\n")
    w("[`cad/chain-carousel-v11/`](../chain-carousel-v11/) (PR #185) is sliced the same way in its own section: "
      "[chain-carousel-v11 (PR #185)](#chain-carousel-v11-pr-185); [`cad/chain-carousel-v12/`](../chain-carousel-v12/) too: "
      "[chain-carousel-v12 (PR #185)](#chain-carousel-v12-pr-185).\n")
    w("![All plates](plates.png)\n")
    w("## Re-running\n")
    w("```bash\n# Bambu Studio for Linux (no login), extracted\n"
      "curl -LO https://github.com/bambulab/BambuStudio/releases/download/v02.08.02.61/BambuStudio_ubuntu24.04-v02.08.02.61-20260820225108.AppImage\n"
      "chmod +x BambuStudio_*.AppImage && ./BambuStudio_*.AppImage --appimage-extract    # -> squashfs-root/\n"
      "sudo apt-get install -y xvfb libosmesa6 libosmesa6-dev weston libwebkit2gtk-4.1-0 libgstreamer-plugins-base1.0-0 gstreamer1.0-plugins-good\n"
      "pip install trimesh shapely rtree                 # audit.py's sections (cadquery for export_printed.py)\n"
      "# optional, for Studio's plate pictures: a headless Wayland display for its OSMesa renderer (glxshim.c is built by slice.py)\n"
      "export XDG_RUNTIME_DIR=/tmp/xdg WAYLAND_DISPLAY=wayland-pd; mkdir -p -m 700 $XDG_RUNTIME_DIR\n"
      "weston --backend=headless --socket=$WAYLAND_DISPLAY --idle-time=0 &\n\n"
      "python export_printed.py                         # STLs from each design's layout.shape() -> <design>/stl/, parts.json\n"
      "python slice.py --bambu squashfs-root --parts     # plates -> <design>/plates/, slice_report.json; --parts: audit.json\n"
      "python previews.py                               # toolpath pictures and plates.png\n"
      "python before_after.py                           # <design>/changes/*_before_after.png\n"
      "python report.py                                 # this README\n\n"
      "# chain-carousel-v11 (PR #185): its own STLs, plates, audit and overview picture\n"
      "python export_printed.py chain-carousel-v11\n"
      "python slice.py --bambu squashfs-root --design chain-carousel-v11 --parts\n"
      "python previews.py chain-carousel-v11              # -> chain-carousel-v11/plates.png\n\n"
      "# chain-carousel-v12 (PR #185): the same; the parts identical to v11's keep v11's audit\n"
      "python export_printed.py chain-carousel-v12\n"
      "python slice.py --bambu squashfs-root --design chain-carousel-v12 --parts --reuse-audit chain-carousel-v11\n"
      "python previews.py chain-carousel-v12              # -> chain-carousel-v12/plates.png\n"
      "python report.py\n```\n")
    w("| File | What it does |\n|---|---|")
    for f, t in [("export_printed.py", "exports each printed part's STL in its CAD frame from the design's own builders (does not run build.py); "
                  "the v2 carriage is exported with its print-only break-off webs"),
                 ("slice.py", "flattens Bambu's system presets (`flatten_bambu_profiles.py`, this repo's script from the "
                  "`copilot/programmatic-access-bambu-h2d` branch), turns each part into its print orientation (`ORIENT`, with the "
                  "reason), packs the plates, runs the Studio CLI once per plate, and parses time, grams, layers and Studio's warnings"),
                 ("audit.py", "mesh checks in print orientation: overhang faces > 50 deg from vertical, layer-by-layer floating "
                  "islands and unsupported area, walls under two line widths, first-layer area"),
                 ("glxshim.c", "lets Studio's CLI render on an OSMesa context under Wayland (fakes the GLX calls its GLEW makes)"),
                 ("previews.py", "draws each plate's extrusion moves from the G-code in its .gcode.3mf, coloured by feature (arcs "
                  "included: Studio's arc fitting writes circles as G2/G3)"),
                 ("chain-carousel-v11/print_variants.py", "v11's printed forms that differ from its assembly shapes (the carriage "
                  "with its break-off webs, the latch carrier without its steel dowel, the side hatch's knob off its acrylic door), "
                  "built from v11's own builders"),
                 ("chain-carousel-v12/print_variants.py", "the same three variants for v12, built from v12's own builders"),
                 ("check_changes.py", "intersects the material a change added with every neighbouring instance at the home pose"),
                 ("before_after.py", "close-ups of the changed parts before and after, in print orientation")]:
        w(f"| [`{f}`]({f}) | {t} |")
    w("")
    w("## Settings\n")
    w(f"Bambu Studio {r0['bambu_studio']} (Linux AppImage, CLI only; nobody logged in). PETG, Bambu's system presets:\n")
    w("| Printer | Machine | Process | Filament | Area used |\n|---|---|---|---|---|")
    w("| H2D | Bambu Lab H2D 0.4 nozzle | 0.20mm Standard @BBL H2D | Bambu PETG Basic @BBL H2D 0.4 nozzle | left nozzle, x 0-325, y 0-320 |")
    w("| A1 mini | Bambu Lab A1 mini 0.4 nozzle | 0.20mm Standard @BBL A1M | Bambu PETG Basic @BBL A1M 0.4 nozzle | 180 x 180 |")
    w("")
    w(f"On top of the presets: {r0['process_overrides']['wall_loops']} walls and {r0['process_overrides']['sparse_infill_density']} sparse "
      f"infill (functional parts), {r0['bed_type']}, supports off (every plate slices clean without them). The H2D slices use the "
      "repo's recipe from `a1_mini_slice_and_send.py`: the filament loaded once per tool, `--filament-map-mode Manual --filament-map 1,2 "
      "--slice 1`. All parts are on filament 1, the left nozzle, which reaches x 0-325 (the right one x 25-350), so the H2D plates are "
      "laid out in 325 x 320. Each plate is its own run and its own `.gcode.3mf` (all under 3 MB, so all are kept).\n")
    w("## Plates\n")
    for d in DESIGNS:
        r = reps[d]
        w(f"### {d}\n")
        w("| Plate | Printer | Parts (quantity) | Time | PETG | Layers | Files |\n|---|---|---|---|---|---|---|")
        tot = {}
        for p in r["plates"]:
            parts = ", ".join(f"{k} x{v}" for k, v in p["parts"].items())
            files = " ".join(f"[{lbl}]({d}/{p[k]})" for k, lbl in (("gcode_3mf", "3mf"), ("studio_png", "Studio"), ("toolpath_png", "toolpaths")) if p.get(k))
            w(f"| {p['plate']} | {p['printer']} | {parts} | {hm(p.get('print_time_s'))} | {p.get('filament_g')} g | {p.get('layers')} | {files} |")
            t = tot.setdefault(p["printer"], [0, 0, 0.0])
            t[0] += 1
            t[1] += p.get("print_time_s") or 0
            t[2] += p.get("filament_g") or 0
        w("")
        w("Totals: " + "; ".join(f"{k}: {v[0]} plate{'s' if v[0] > 1 else ''}, {hm(v[1])}, {v[2]:.0f} g" for k, v in tot.items())
          + f"; all: {r['total_print_time_h']} h of printing, {r['total_filament_g']:.0f} g of PETG.\n")
        w("The station plates (A1 mini) get a 3 mm outer brim for the small parts; everything else prints without brim or support.\n")
    w("## Printability audit\n")
    w("Per part, in print orientation, from `audit.py` (mesh) and from slicing the part alone with supports off. "
      "Overhang: downward faces more than 50 deg from vertical, not on the bed (bridges and hole roofs included). "
      "Floating islands: regions with nothing under them in the layer below. Thin: layers with a region under 0.84 mm "
      "(two 0.42 mm lines) wide.\n")
    for d in DESIGNS:
        a = audits[d]
        w(f"### {d}\n")
        w("| Part | Qty | Orientation | On the bed (mm) | First layer | Overhang > 50 deg | Floating islands | Thin layers | Studio, supports off | Alone | Notes |")
        w("|---|---|---|---|---|---|---|---|---|---|---|")
        for k, v in a.items():
            m, s = v["mesh"], v["studio_supports_off"]
            warn = "; ".join(s.get("slicer_warnings") or []) or "no warnings"
            note = NOTES[d].get(k) or COMMON.get(k, "")
            sz = " x ".join(f"{x:g}" for x in m["size_mm"])
            w(f"| {k} | {v['qty']} | {v['why'] if v['why'].startswith('as ') else orient_txt(v['orientation']) + ': ' + v['why']} | {sz} | {m.get('first_layer_mm2', '-')} mm2 | "
              f"{m['overhang_area_mm2']} mm2 | {m.get('n_floating_islands', '-')} | {m.get('thin_wall_layers', '-')} | {warn} | "
              f"{s.get('print_time')}, {s.get('filament_g')} g | {note} |")
        w("")
    w("## Changes made for printability\n")
    w("1. **paternoster `gondola()`** (`cad/paternoster/parts.py`, saddle under the auger): the seat was a V-shaped prism standing "
      "on its apex, cut by the 13.1 mm tube clearance, which left two cheeks at |y| 12.2-18 whose undersides started 8 mm above "
      "the cross bar. Studio (supports off): \"floating regions\". The seat is now a 36 x 12 mm block on the bar minus the same "
      "R 13.1 tube cut, so the cheeks stand on the bar: same 0.6 mm clearance round the tube, same top and width, +1.7 cm3. "
      "The added material is under the old cheeks, inside the gondola's own outline; `check_changes.py` (added material against "
      "the neighbouring instances) did not finish on the loaded runner, so the clearance rests on the full interference check.\n\n"
      "   ![gondola before/after](paternoster/changes/gondola_before_after.png)\n")
    w("2. **chain-carousel-v2 `tab_hook()` / `carriage()`** (`cad/chain-carousel-v2/parts.py`): new `print_web=False` argument. "
      "Printed plate-down (the only orientation without big overhangs: on edge it has six floating islands and 3800 mm2 of "
      "overhang), each tab hook's finger is a 9.2 mm cantilever from its spine over the 1.55 mm tab slot; Studio: \"floating "
      "cantilever\". With `print_web=True` a 0.8 mm web closes the slot's -u mouth so the finger prints as a bridge; cut it off "
      "flush after printing. The assembly (`layout.shape('carriage')`, build.py's stl/, the interference checks) is drawn "
      "without it, so nothing that mates with the carriage changed; `export_printed.py` exports the print variant.\n\n"
      "   ![carriage before/after](chain-carousel-v2/changes/carriage_before_after.png)\n")
    w("## Open points (not changed)\n")
    w("* No fastener holes are modelled in paternoster's `hold_bracket` and `fork_arm`, or in either design's `fork`.\n"
      "* Press and pin holes (4.0 mm stub pin, 4.15 mm clevis pin, 7.0 mm bushings) are drawn at nominal size; printed holes run "
      "0.1-0.2 mm small, so plan to ream. Studio's circle compensation is off (stock).\n")
    v11_section(w)
    v12_section(w)
    w("## Not verified\n")
    w("* Nothing here has been printed. Times and grams are Studio's estimates.\n"
      "* The plates use the H2D's left nozzle only; the bed type is assumed (Textured PEI) and must match the plate on the printer.\n"
      "* The toolpath pictures are drawn from the G-code, not screenshots of Studio's Preview tab.\n")
    (HERE / "README.md").write_text("\n".join(L))
    print("README.md written")


if __name__ == "__main__":
    main()
