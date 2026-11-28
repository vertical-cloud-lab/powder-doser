#!/usr/bin/env python3
"""Write fc1.kicad_pro (net classes, JLCPCB-safe design rules) from fc1_design.py."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fc1_design as D

def nc(name, clearance, track, prio):
    return {"name": name, "clearance": clearance, "track_width": track, "via_diameter": 0.6, "via_drill": 0.3,
            "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
            "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0,
            "schematic_color": "rgba(0, 0, 0, 0.000)", "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": prio}

classes = [nc("Default", D.DEFAULT_CLEARANCE, D.DEFAULT_TRACK, 2147483647)]
patterns = []
for i, (name, c) in enumerate(D.NETCLASS.items()):
    classes.append(nc(name, c["clearance"], c["track"], i))
    patterns += [{"netclass": name, "pattern": "/" + n} for n in c["nets"]]

pro = {
  "board": {
    "3dviewports": [],
    "design_settings": {
      "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2, "copper_text_size_h": 1.5,
                   "copper_text_size_v": 1.5, "copper_text_thickness": 0.3, "silk_line_width": 0.12,
                   "silk_text_size_h": 1.0, "silk_text_size_v": 1.0, "silk_text_thickness": 0.15,
                   "pads": {"drill": 0.8, "height": 1.6, "width": 1.6}, "zones": {"min_clearance": 0.25}},
      "rules": {"min_clearance": 0.15, "min_connection": 0.0, "min_copper_edge_clearance": 0.3,
                "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25, "min_microvia_diameter": 0.2,
                "min_microvia_drill": 0.1, "min_resolved_spokes": 1, "min_silk_clearance": 0.0,
                "min_text_height": 0.7, "min_text_thickness": 0.08, "min_through_hole_diameter": 0.3,
                "min_track_width": 0.15, "min_via_annular_width": 0.1, "min_via_diameter": 0.5,
                "solder_mask_to_copper_clearance": 0.0, "use_height_for_length_calcs": True},
      "rule_severities": {"lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore"},
      "track_widths": [0.0, 0.25, 0.3, 0.4], "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}],
      "zones_allow_external_fillets": False
    },
    "ipc2581": {}, "layer_presets": [], "viewports": []
  },
  "boards": [], "cvpcb": {"equivalence_files": []},
  "erc": {"erc_exclusions": [], "meta": {"version": 0}, "pin_map": [], "rule_severities": {}},
  "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
  "meta": {"filename": "fc1.kicad_pro", "version": 3},
  "net_settings": {"classes": classes, "meta": {"version": 4}, "net_colors": None,
                   "netclass_assignments": None, "netclass_patterns": patterns},
  "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
  "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
  "sheets": [], "text_variables": {}
}
json.dump(pro, open(os.path.join(HERE, "fc1.kicad_pro"), "w"), indent=2)
print("wrote fc1.kicad_pro")
