#!/usr/bin/env python3
"""Apply the note-25 pre-fab zone fix to run-3 candidate 2.

Quilter's run-3 exports carry a full-board zone on ``In2.Cu`` ("Power
Layer 2") with ``(net 0)`` / ``<no net>``.  Because a no-net zone keeps no
clearance from real copper, it is the source of *all* 152 DRC errors on
every candidate (76 ``clearance`` + 76 ``hole_clearance``); nothing
electrical depends on it.  Note 25's recommendation for the chosen board
(candidate 2) is: assign that zone to ``GND`` and refill, which clears the
errors and yields a second solid ground plane under the routing layers.

This script applies exactly that, without touching the verbatim Quilter
output in ``candidate_2/``:

1. load ``candidate_2/test_module_unplaced.kicad_pcb`` (KiCad 7 ``pcbnew``);
2. assign every ``<no net>`` zone on ``In2.Cu`` to net ``GND``;
3. refill all zones (``pcbnew.ZONE_FILLER``);
4. save to ``candidate_2_fixed/test_module_unplaced.kicad_pcb`` (the
   companion ``.kicad_pro`` is copied unchanged);
5. re-run DRC + connectivity and write ``candidate_2_fixed/fix_report.json``.

Run from this directory:  python3 fix_candidate2_in2_zone.py
Requires KiCad 7 (``pcbnew`` python module); read-only w.r.t. candidate_2/.

Reproducibility caveat: unlike ``build_starter_board.py``'s byte-for-byte
output, ``pcbnew.SaveBoard`` does not serialize footprints in a stable
order, so re-runs yield an *electrically identical* board whose file-level
element ordering may differ.  Verify re-runs against
``candidate_2_fixed/fix_report.json`` (DRC buckets, zone fill, ratsnest),
not file hashes.
"""

import json
import os
import re
import shutil

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(HERE, "candidate_2")
DST_DIR = os.path.join(HERE, "candidate_2_fixed")
BOARD_NAME = "test_module_unplaced.kicad_pcb"
PRO_NAME = "test_module_unplaced.kicad_pro"


def drc_counts(board_path):
    """Run pcbnew DRC on a board file and bucket violations by type."""
    board = pcbnew.LoadBoard(board_path)
    report = board_path + ".drc"
    pcbnew.WriteDRCReport(board, report, pcbnew.EDA_UNITS_MILLIMETRES, True)
    buckets = {}
    with open(report, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"\[(\w+)\]", line.strip())
            if m:
                buckets[m.group(1)] = buckets.get(m.group(1), 0) + 1
    os.remove(report)
    unconnected = board.GetConnectivity().GetUnconnectedCount(True)
    return buckets, unconnected


def main():
    os.makedirs(DST_DIR, exist_ok=True)
    src_board = os.path.join(SRC_DIR, BOARD_NAME)
    dst_board = os.path.join(DST_DIR, BOARD_NAME)

    before_drc, before_unconnected = drc_counts(src_board)

    board = pcbnew.LoadBoard(src_board)
    gnd = board.GetNetsByName()["GND"]
    fixed = []
    for zone in board.Zones():
        layer = board.GetLayerName(zone.GetFirstLayer())
        if zone.GetNetCode() == 0:
            zone.SetNet(gnd)
            fixed.append(layer)
    if not fixed:
        raise SystemExit("no <no net> zone found — nothing to fix")

    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(dst_board, board)
    shutil.copyfile(os.path.join(SRC_DIR, PRO_NAME),
                    os.path.join(DST_DIR, PRO_NAME))

    after_drc, after_unconnected = drc_counts(dst_board)

    # Confirm the reassigned zone's fill really is GND copper on In2.Cu.
    check = pcbnew.LoadBoard(dst_board)
    zones_after = [
        {
            "layer": check.GetLayerName(z.GetFirstLayer()),
            "net": z.GetNetname(),
            # GetFilledArea() is in KiCad internal units (1 mm = 1e6 IU)
            "filled_area_mm2": round(z.GetFilledArea() / 1e12, 1),
        }
        for z in check.Zones()
    ]

    report = {
        "source": os.path.relpath(src_board, HERE),
        "output": os.path.relpath(dst_board, HERE),
        "zones_reassigned_to_GND": fixed,
        "zones_after": zones_after,
        "drc_before": before_drc,
        "drc_after": after_drc,
        "unconnected_before": before_unconnected,
        "unconnected_after": after_unconnected,
        "kicad_version": pcbnew.GetBuildVersion(),
    }
    out = os.path.join(DST_DIR, "fix_report.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps(report, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
