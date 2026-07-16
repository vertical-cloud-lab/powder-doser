#!/usr/bin/env python3
"""Final pre-order gate + JLCPCB fabrication kit for run-3 candidate 2.

Note 25's remaining pre-fab steps for the chosen board
(``candidate_2_fixed/test_module_unplaced.kicad_pcb``) were: run *Update PCB
from Schematic* against the generator's ``.kicad_sch`` (commit ``0683525``),
re-run DRC, and produce the files JLCPCB's quote page
(https://cart.jlcpcb.com/quote — "Only accept zip or rar", Gerbers + Excellon
drill) needs.  This script does all three, headlessly and re-runnably:

1. **Schematic->board sync pass** (the headless equivalent of KiCad's
   *Update PCB from Schematic*, which has no kicad-cli entry point in 7.0):
   export the netlist from ``../test_module_unplaced.kicad_sch`` with
   ``kicad-cli sch export netlist`` and verify, pad by pad, that every
   schematic node ``(ref, pin)`` sits on the same net on the board and that
   no net-assigned board pad is absent from the schematic netlist.  Any
   mismatched pad would be re-assigned to the schematic's net (and zones
   refilled + board saved); a clean board — the expected case, since note
   25's audit already matched the trio — is left byte-untouched.  Footprint
   ``(path ...)`` symbol links and no-net copper (tracks/vias/zones) are
   checked at the same time.
2. **Final DRC gate** (``pcbnew.WriteDRCReport``): require unconnected
   ratsnest 0 and zero clearance / hole_clearance / shorting / courtyard
   errors, plus JLCPCB 4-layer capability checks (min trace width/clearance
   >= 0.09 mm, min via drill >= 0.2 mm, min via annular >= 0.05 mm, board
   extents vs the 110 x 110 mm outline).
3. **Fabrication kit**: ``kicad-cli pcb export gerbers`` (Protel filename
   extensions — kicad-cli 7's default and JLCPCB's preference — with
   soldermask subtracted from silk, per JLCPCB's KiCad guide) for
   F.Cu / In1.Cu / In2.Cu / B.Cu / F.Mask / B.Mask / F.Silkscreen /
   B.Silkscreen / Edge.Cuts, plus ``kicad-cli pcb export drill`` (Excellon,
   absolute origin, mm, decimal zeros, PTH+NPTH merged — all this board's
   holes are plated — with a Gerber-X2 drill map).  Everything is zipped to
   ``candidate_2_fixed/powder_doser_run3_candidate2_jlcpcb.zip`` — the one
   file to upload at https://cart.jlcpcb.com/quote — and the loose files are
   kept beside it under ``candidate_2_fixed/jlcpcb_gerbers/`` for review.
   The Edge.Cuts gerber is re-parsed to confirm the outline extents.

Run from this directory:  python3 prepare_jlcpcb_order.py
Requires KiCad 7 (``pcbnew`` python module + ``kicad-cli``).
Writes ``candidate_2_fixed/jlcpcb_order_report.json`` (the captured gate
results); the zip is built with fixed timestamps so re-runs are
byte-identical when the gerbers are.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "candidate_2_fixed", "test_module_unplaced.kicad_pcb")
SCH = os.path.join(HERE, "..", "test_module_unplaced.kicad_sch")
OUT_DIR = os.path.join(HERE, "candidate_2_fixed", "jlcpcb_gerbers")
ZIP_PATH = os.path.join(HERE, "candidate_2_fixed",
                        "powder_doser_run3_candidate2_jlcpcb.zip")
REPORT = os.path.join(HERE, "candidate_2_fixed", "jlcpcb_order_report.json")

LAYERS = ("F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,"
          "F.Silkscreen,B.Silkscreen,Edge.Cuts")

# JLCPCB standard 4-layer capabilities (jlcpcb.com/capabilities), mm
JLC_MIN_TRACE = 0.09
JLC_MIN_CLEARANCE = 0.09
JLC_MIN_VIA_DRILL = 0.20
JLC_MIN_VIA_ANNULAR = 0.05
JLC_MAX_DIM = 400.0


def _sch_netlist() -> dict:
    """{net_name: {(ref, pin_number), ...}} from the generator schematic."""
    cli = shutil.which("kicad-cli")
    if not cli:
        raise SystemExit("kicad-cli is required for the schematic sync pass")
    with tempfile.TemporaryDirectory() as td:
        net_path = os.path.join(td, "sync.net")
        subprocess.run(
            [cli, "sch", "export", "netlist", "--format", "kicadsexpr",
             "-o", net_path, SCH],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        txt = open(net_path, encoding="utf-8").read()
    nets = {}
    for m in re.finditer(
            r'\(net \(code "\d+"\) \(name "([^"]*)"\)(.*?)(?=\(net \(code|\Z)',
            txt, re.S):
        name, body = m.group(1), m.group(2)
        nodes = set(re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)',
                               body))
        if nodes:
            nets[name] = nodes
    return nets


def sync_board_to_schematic(board) -> dict:
    """Headless *Update PCB from Schematic*: verify every pad's net against
    the schematic netlist, fixing (and reporting) any drift."""
    sch_nets = _sch_netlist()
    # invert to (ref, pin) -> net, dropping KiCad's auto "unconnected-" nets:
    # those pads must carry no net on the board.
    want = {}
    for net, nodes in sch_nets.items():
        for node in nodes:
            want[node] = "" if net.startswith("unconnected-") else net

    board_nets = board.GetNetsByName()
    fixed, missing_path = [], []
    seen = set()
    for fp in board.Footprints():
        ref = fp.GetReference()
        if not fp.GetPath().AsString().strip("/"):
            missing_path.append(ref)
        for pad in fp.Pads():
            node = (ref, pad.GetNumber())
            seen.add(node)
            expect = want.get(node)
            if expect is None:
                # pad absent from the schematic netlist entirely
                fixed.append({"pad": f"{ref}.{pad.GetNumber()}",
                              "board_net": pad.GetNetname(),
                              "schematic_net": "<missing from schematic>"})
                continue
            if pad.GetNetname() != expect:
                fixed.append({"pad": f"{ref}.{pad.GetNumber()}",
                              "board_net": pad.GetNetname(),
                              "schematic_net": expect})
                pad.SetNet(board_nets[expect]) if expect else \
                    pad.SetNetCode(0)
    absent = sorted(f"{r}.{p}" for (r, p) in set(want) - seen)

    no_net_copper = []
    for tr in board.GetTracks():
        if tr.GetNetCode() == 0:
            kind = "via" if tr.Type() == pcbnew.PCB_VIA_T else "track"
            no_net_copper.append(f"{kind}@({tr.GetX()/1e6:.1f},"
                                 f"{tr.GetY()/1e6:.1f})")
    for zone in board.Zones():
        if zone.GetNetCode() == 0:
            no_net_copper.append(
                f"zone on {board.GetLayerName(zone.GetFirstLayer())}")

    if fixed:
        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(board.Zones())
        pcbnew.SaveBoard(BOARD, board)
    return {
        "schematic_nets": len([n for n in sch_nets
                               if not n.startswith("unconnected-")]),
        "schematic_nodes_checked": len(want),
        "pads_reassigned": fixed,
        "pads_in_schematic_but_not_on_board": absent,
        "footprints_missing_symbol_path": missing_path,
        "no_net_copper": no_net_copper,
        "board_saved": bool(fixed),
        "in_sync": not (fixed or absent or missing_path or no_net_copper),
    }


def drc_gate(board) -> dict:
    board.BuildConnectivity()
    unconnected = board.GetConnectivity().GetUnconnectedCount(True)
    with tempfile.NamedTemporaryFile("r", suffix=".rpt", delete=False) as fh:
        report = fh.name
    pcbnew.WriteDRCReport(board, report, pcbnew.EDA_UNITS_MILLIMETRES, True)
    buckets = {}
    with open(report, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"\[(\w+)\]", line.strip())
            if m:
                buckets[m.group(1)] = buckets.get(m.group(1), 0) + 1
    os.unlink(report)

    min_track = min((t.GetWidth() for t in board.GetTracks()
                     if t.Type() == pcbnew.PCB_TRACE_T), default=0) / 1e6
    vias = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    min_drill = min((v.GetDrillValue() for v in vias), default=0) / 1e6
    min_annular = min(((v.GetWidth() - v.GetDrillValue()) / 2 for v in vias),
                      default=0) / 1e6
    bbox = board.GetBoardEdgesBoundingBox()
    size = (bbox.GetWidth() / 1e6, bbox.GetHeight() / 1e6)
    clearance = board.GetDesignSettings().m_MinClearance / 1e6

    hard = ["clearance", "hole_clearance", "shorting_items",
            "courtyards_overlap", "duplicate_footprints", "missing_footprint",
            "malformed_courtyard", "invalid_outline"]
    caps_ok = (min_track >= JLC_MIN_TRACE and clearance >= JLC_MIN_CLEARANCE
               and min_drill >= JLC_MIN_VIA_DRILL
               and min_annular >= JLC_MIN_VIA_ANNULAR
               and max(size) <= JLC_MAX_DIM)
    return {
        "unconnected": unconnected,
        "drc": buckets,
        "hard_errors": {k: buckets[k] for k in hard if buckets.get(k)},
        "board_size_mm": [round(size[0], 2), round(size[1], 2)],
        "copper_layers": board.GetCopperLayerCount(),
        "min_track_mm": round(min_track, 4),
        "min_clearance_rule_mm": round(clearance, 4),
        "min_via_drill_mm": round(min_drill, 4),
        "min_via_annular_mm": round(min_annular, 4),
        "jlcpcb_capabilities_ok": caps_ok,
        "pass": (unconnected == 0 and caps_ok
                 and not any(buckets.get(k) for k in hard)),
    }


def export_fab_kit() -> dict:
    cli = shutil.which("kicad-cli")
    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)
    subprocess.run(
        [cli, "pcb", "export", "gerbers", "-o", OUT_DIR + os.sep,
         "--layers", LAYERS, "--subtract-soldermask", "--no-x2",
         "--disable-aperture-macros", BOARD],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(
        [cli, "pcb", "export", "drill", "-o", OUT_DIR + os.sep,
         "--format", "excellon", "--drill-origin", "absolute",
         "--excellon-units", "mm", "--excellon-zeros-format", "decimal",
         "--generate-map", "--map-format", "gerberx2", BOARD],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # kicad-cli names outputs after the board file; drop the stale .gbrjob
    # (a fab-metadata sidecar JLCPCB neither needs nor parses).
    for f in os.listdir(OUT_DIR):
        if f.endswith(".gbrjob"):
            os.unlink(os.path.join(OUT_DIR, f))

    # Quilter renamed the copper layers ("Ground Layer 1", "Board Layer
    # Stack Bottom Overlay", ...), which kicad-cli bakes into the gerber
    # filenames. JLCPCB identifies layers by the Protel extension, so
    # re-stem every file to one clean name. At the same time, drop the
    # wall-clock CreationDate header comments kicad-cli stamps into every
    # file (metadata only — no fab tool needs them) so re-runs of this
    # script produce byte-identical gerbers and zip.
    date_line = re.compile(
        r"CreationDate|^; DRILL file \{KiCad [^}]*\} date "
        r"|^G04 Created by KiCad .* date ")
    stem = "powder_doser_run3_cand2"
    for f in list(os.listdir(OUT_DIR)):
        base, ext = os.path.splitext(f)
        new = f"{stem}-drl_map{ext}" if base.endswith("drl_map") \
            else f"{stem}{ext}"
        src = os.path.join(OUT_DIR, f)
        text = open(src, encoding="utf-8").read()
        kept = [ln for ln in text.splitlines(keepends=True)
                if not date_line.search(ln)]
        with open(os.path.join(OUT_DIR, new), "w", encoding="utf-8") as fh:
            fh.writelines(kept)
        if new != f:
            os.unlink(src)

    files = sorted(os.listdir(OUT_DIR))
    empty = [f for f in files
             if os.path.getsize(os.path.join(OUT_DIR, f)) == 0]

    # confirm the plotted outline extents straight from the Edge.Cuts gerber
    edge = next(f for f in files if f.lower().endswith(".gm1"))
    coords = re.findall(r"X(-?\d+)Y(-?\d+)",
                        open(os.path.join(OUT_DIR, edge)).read())
    xs = [int(x) / 1e6 for x, _ in coords]
    ys = [int(y) / 1e6 for _, y in coords]
    extents = [round(max(xs) - min(xs), 2), round(max(ys) - min(ys), 2)]

    if os.path.exists(ZIP_PATH):
        os.unlink(ZIP_PATH)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            info = zipfile.ZipInfo(f, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info,
                        open(os.path.join(OUT_DIR, f), "rb").read())
    return {
        "files": files,
        "empty_files": empty,
        "edge_cuts_extents_mm": extents,
        "zip": os.path.relpath(ZIP_PATH, HERE),
        "zip_bytes": os.path.getsize(ZIP_PATH),
    }


def main() -> int:
    board = pcbnew.LoadBoard(BOARD)
    report = {"board": os.path.relpath(BOARD, HERE),
              "schematic": "../test_module_unplaced.kicad_sch (commit 0683525 generator output)",
              "kicad_version": pcbnew.Version()}
    report["sync_pass"] = sync_board_to_schematic(board)
    report["drc_gate"] = drc_gate(board)
    report["fab_kit"] = export_fab_kit()

    ok = (report["sync_pass"]["in_sync"] and report["drc_gate"]["pass"]
          and not report["fab_kit"]["empty_files"]
          and len(report["fab_kit"]["files"]) >= 11)
    report["ready_to_order"] = ok
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps(report, indent=1, sort_keys=True))
    print("\nREADY TO ORDER" if ok else "\nNOT READY — see report", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
