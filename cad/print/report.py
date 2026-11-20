"""Write README.md from slice_report.json and audit.json of both designs (run after slice.py and previews.py)."""
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


def hm(s: int | None) -> str:
    if not s:
        return "-"
    h, m = divmod(round(s / 60), 60)
    return f"{h} h {m:02d} min" if h else f"{m} min"


def orient_txt(spec) -> str:
    return "as drawn" if not spec else ", ".join(f"{d:+d} deg about {a}" for a, d in spec)


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
    w("![All plates](plates.png)\n")
    w("## Re-running\n")
    w("```bash\n# Bambu Studio for Linux (no login), extracted\n"
      "curl -LO https://github.com/bambulab/BambuStudio/releases/download/v02.08.02.61/BambuStudio_ubuntu24.04-v02.08.02.61-20260820225108.AppImage\n"
      "chmod +x BambuStudio_*.AppImage && ./BambuStudio_*.AppImage --appimage-extract    # -> squashfs-root/\n"
      "sudo apt-get install -y xvfb libosmesa6 weston libwebkit2gtk-4.1-0 libgstreamer-plugins-base1.0-0 gstreamer1.0-plugins-good\n"
      "# optional, for Studio's plate pictures: a headless Wayland display for its OSMesa renderer (glxshim.c is built by slice.py)\n"
      "export XDG_RUNTIME_DIR=/tmp/xdg WAYLAND_DISPLAY=wayland-pd; mkdir -p -m 700 $XDG_RUNTIME_DIR\n"
      "weston --backend=headless --socket=$WAYLAND_DISPLAY --idle-time=0 &\n\n"
      "python export_printed.py                         # STLs from each design's layout.shape() -> <design>/stl/, parts.json\n"
      "python slice.py --bambu squashfs-root --parts     # plates -> <design>/plates/, slice_report.json; --parts: audit.json\n"
      "python previews.py                               # toolpath pictures and plates.png\n"
      "python before_after.py                           # <design>/changes/*_before_after.png\n"
      "python report.py                                 # this README\n```\n")
    w("| File | What it does |\n|---|---|")
    for f, t in [("export_printed.py", "exports each printed part's STL in its CAD frame from the design's own builders (does not run build.py); "
                  "the v2 carriage is exported with its print-only break-off webs"),
                 ("slice.py", "flattens Bambu's system presets (`flatten_bambu_profiles.py`, this repo's script from the "
                  "`copilot/programmatic-access-bambu-h2d` branch), turns each part into its print orientation (`ORIENT`, with the "
                  "reason), packs the plates, runs the Studio CLI once per plate, and parses time, grams, layers and Studio's warnings"),
                 ("audit.py", "mesh checks in print orientation: overhang faces > 50 deg from vertical, layer-by-layer floating "
                  "islands and unsupported area, walls under two line widths, first-layer area"),
                 ("glxshim.c", "lets Studio's CLI render on an OSMesa context under Wayland (fakes the GLX calls its GLEW makes)"),
                 ("previews.py", "draws each plate's extrusion moves from the G-code in its .gcode.3mf, coloured by feature"),
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
    w("## Not verified\n")
    w("* Nothing here has been printed. Times and grams are Studio's estimates.\n"
      "* The plates use the H2D's left nozzle only; the bed type is assumed (Textured PEI) and must match the plate on the printer.\n"
      "* The toolpath pictures are drawn from the G-code, not screenshots of Studio's Preview tab.\n")
    (HERE / "README.md").write_text("\n".join(L))
    print("README.md written")


if __name__ == "__main__":
    main()
