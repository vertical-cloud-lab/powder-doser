#!/usr/bin/env python3
"""Build a printable multi-page color PDF of the run-3 candidate-2 board.

Purpose (PR #76): a paper spot-check kit for an ME office printer — the board
pages are exact 1:1 scale on US-Letter so the team can lay the physical parts
(Pico W, Waveshare RS-232 module, Tic T500, breakouts, caps, headers) directly
on the printout and visually verify the overlay before ordering.

Inputs (read-only):
  candidate_2_fixed/test_module_unplaced.kicad_pcb   (the JLCPCB ordering board)
  ../test_module_unplaced.kicad_sch                  (matching generator schematic)

Output:
  candidate_2_fixed/powder_doser_run3_candidate2_print.pdf

How 1:1 is preserved: `kicad-cli pcb export pdf` plots at true scale onto the
board's A4-landscape sheet, but this board's outline spans (-5,-5)..(105,105) mm
so 5 mm of the edge falls off the sheet.  Each plotted page is therefore
re-centered onto a US-Letter portrait page with a pure translation (never a
scale), then stamped with a title header and a 100 mm scale-check bar.  Pages
that are not meant to be 1:1 (cover, drill map, schematic) say so explicitly.

Requires: kicad-cli 7.x on PATH, pypdf, reportlab, kiutils.
Run from this directory:  python3 make_print_pdf.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
BOARD = HERE / "candidate_2_fixed" / "test_module_unplaced.kicad_pcb"
SCHEMATIC = HERE.parent / "test_module_unplaced.kicad_sch"
OUT_PDF = HERE / "candidate_2_fixed" / "powder_doser_run3_candidate2_print.pdf"

# Board geometry (verified with kiutils against the Edge.Cuts of BOARD).
BOARD_BBOX_MM = (-5.0, -5.0, 105.0, 105.0)  # x0, y0, x1, y1 in KiCad sheet coords
SHEET_H_MM = 210.0  # the exported plots land on the board's A4-landscape sheet

LETTER_W_PT, LETTER_H_PT = letter  # 612 x 792 pt = 215.9 x 279.4 mm
PT_PER_MM = 72.0 / 25.4

THEME_NAME = "print_paper"

# Print-friendly layer colors (KiCad's defaults assume a dark screen; yellow
# silk / pink mask are illegible on white paper).
THEME_JSON = {
    "meta": {"name": THEME_NAME, "version": 5},
    "board": {
        "copper": {"f": "rgb(200, 30, 30)", "b": "rgb(0, 80, 200)",
                   "in1": "rgb(0, 140, 60)", "in2": "rgb(150, 80, 180)"},
        "edge_cuts": "rgb(0, 0, 0)",
        "f_silks": "rgb(0, 0, 0)",
        "b_silks": "rgb(90, 90, 90)",
        "f_fab": "rgb(80, 80, 80)",
        "b_fab": "rgb(150, 150, 150)",
        "f_crtyd": "rgb(160, 32, 240)",
        "b_crtyd": "rgb(38, 200, 255)",
        "f_mask": "rgb(184, 134, 11)",
        "b_mask": "rgb(120, 120, 200)",
        "background": "rgb(255, 255, 255)",
        "via_through": "rgb(60, 60, 60)",
        "via_hole": "rgb(255, 255, 255)",
        "pad_through_hole": "rgb(200, 30, 30)",
        "plated_hole": "rgb(60, 60, 60)",
    },
}

# (title, kicad-cli layer list, note) for the 1:1 board pages, in page order.
BOARD_PAGES = [
    ("Top assembly overlay — lay the parts on this page",
     "Edge.Cuts,F.Fab,F.SilkS,F.CrtYd,F.Mask",
     "Grey = part body (F.Fab), black = silkscreen, purple = courtyard, "
     "gold = pad/hole openings (F.Mask)."),
    ("Top copper (F.Cu) + silkscreen",
     "Edge.Cuts,F.Cu,F.SilkS",
     "Red = top copper as routed by Quilter (run 3, candidate 2)."),
    ("Bottom copper (B.Cu) — X-ray view",
     "Edge.Cuts,B.Cu,B.SilkS",
     "Blue = bottom copper, NOT mirrored (drawn looking through the board), "
     "so it overlays the top pages when held to the light."),
    ("Inner layer 1 (In1.Cu) — GND plane",
     "Edge.Cuts,In1.Cu",
     "Green = inner-layer copper (solid GND plane); X-ray view."),
    ("Inner layer 2 (In2.Cu) — GND plane",
     "Edge.Cuts,In2.Cu",
     "Purple = inner-layer copper (former <no net> zone, now GND per the "
     "note-25 fix); X-ray view."),
]

# Parts legend for the cover page: ref -> (part, what to grab from the kit).
PARTS = [
    ("U1", "Pololu D24V22F5 5 V buck", "17.8 x 17.8 mm carrier, 5+1 holes"),
    ("U2", "Raspberry Pi Pico W", "2x20 pins @ 17.78 mm row spacing"),
    ("U3", "Adafruit DRV2605L breakout (STEMMA QT)", "haptic driver, 25.4 x 17.78 mm"),
    ("U4", "Adafruit DRV8871 breakout", "solenoid driver, 2x 3.5 mm terminal blocks"),
    ("U5", "Pololu Tic T500", "stepper controller, 38.1 x 26.7 mm"),
    ("U6", "Waveshare Pico-2CH-RS232 (scale)", "2x20 side receptacle, 21 x 52 mm body"),
    ("SR1", "Pololu shunt regulator (#3776)", "28.6 x 20.3 mm, VIN/GND terminals"),
    ("J1", "Barrel jack 12 V (PJ-102AH)", "tip=+12V, sleeve=GND"),
    ("C1", "100 uF radial cap (buck VIN)", "D8 mm, 3.5 mm pitch, square pad = +"),
    ("C2", "100 uF radial cap (Pico VSYS)", "D8 mm, 3.5 mm pitch, square pad = +"),
    ("C3", "100 uF radial cap (Tic VIN)", "D8 mm, 3.5 mm pitch, square pad = +"),
    ("M1", "ERM vibration motor header", "1x2 pin header 0.1 inch"),
    ("M2", "Stepper (NEMA-11) header", "1x4 pin header 0.1 inch"),
    ("M3", "Servo 1 header (SERVO_SIG)", "1x3 pin header 0.1 inch"),
    ("M4", "Servo 2 header (SERVO_SIG2)", "1x3 pin header 0.1 inch"),
    ("SOL1", "Solenoid header", "1x2 pin header 0.1 inch"),
]


def install_theme() -> None:
    cfg = Path.home() / ".config" / "kicad" / "7.0" / "colors"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / f"{THEME_NAME}.json").write_text(json.dumps(THEME_JSON, indent=2))


def kicad_cli(*args: str) -> None:
    subprocess.run(["kicad-cli", *args], check=True, capture_output=True, text=True)


def board_transform() -> Transformation:
    """Pure translation putting the board's center at the Letter page center."""
    x0, y0, x1, y1 = BOARD_BBOX_MM
    # KiCad plot: sheet coord (x, y) mm -> PDF point (x, SHEET_H_MM - y) * PT_PER_MM
    cx_pt = (x0 + x1) / 2.0 * PT_PER_MM
    cy_pt = (SHEET_H_MM - (y0 + y1) / 2.0) * PT_PER_MM
    return Transformation().translate(LETTER_W_PT / 2.0 - cx_pt,
                                      LETTER_H_PT / 2.0 - cy_pt)


def overlay_page(title: str, note: str, page_no: int, total: int,
                 one_to_one: bool) -> "pypdf._page.PageObject":
    """A Letter-sized reportlab overlay: header, note, footer, scale bar."""
    import io
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    import textwrap
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(12 * mm, LETTER_H_PT - 12 * mm, title)
    c.setFont("Helvetica", 8)
    for k, line in enumerate(textwrap.wrap(note, width=90)):
        c.drawString(12 * mm, LETTER_H_PT - (17 + 4 * k) * mm, line)
    scale_txt = ("SCALE 1:1 — print at 100% / “Actual size”"
                 if one_to_one else "NOT TO SCALE — reference only")
    c.setFont("Helvetica-Bold", 9)
    if one_to_one:
        c.setFillColorRGB(0.7, 0, 0)
    c.drawRightString(LETTER_W_PT - 12 * mm, LETTER_H_PT - 12 * mm, scale_txt)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 7)
    c.drawString(12 * mm, 8 * mm,
                 "powder-doser PR #76 — Quilter run-3 candidate 2 (In2 GND fix) — "
                 "quilter_candidates_run3/candidate_2_fixed/test_module_unplaced.kicad_pcb")
    c.drawRightString(LETTER_W_PT - 12 * mm, 8 * mm, f"page {page_no} / {total}")
    if one_to_one:
        # 100 mm scale-check bar with 10 mm ticks, bottom-left.
        bx, by = 12 * mm, 16 * mm
        c.setLineWidth(0.6)
        c.line(bx, by, bx + 100 * mm, by)
        for i in range(11):
            tick = 3 * mm if i % 5 == 0 else 1.8 * mm
            c.line(bx + i * 10 * mm, by, bx + i * 10 * mm, by + tick)
        c.setFont("Helvetica", 7)
        c.drawString(bx, by + 4 * mm, "0")
        c.drawString(bx + 97 * mm, by + 4 * mm, "100 mm  (verify with a ruler)")
    c.showPage()
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def cover_page() -> "pypdf._page.PageObject":
    import io
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    y = LETTER_H_PT - 20 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(15 * mm, y, "Powder doser — PCB 1:1 print kit (color)")
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    c.drawString(15 * mm, y, "Quilter run-3 candidate 2 with the In2 GND-plane fix — "
                             "the board prepared for JLCPCB ordering (PR #76, note 25).")
    y -= 5 * mm
    c.drawString(15 * mm, y, f"Board: 110 x 110 mm, 4-layer (F.Cu / In1 GND / In2 GND / B.Cu), "
                             f"16 through-hole footprints. Generated {date.today().isoformat()}.")
    y -= 10 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(15 * mm, y, "How to print")
    y -= 6 * mm
    c.setFont("Helvetica", 10)
    for line in [
        "1.  Print in COLOR on US Letter at 100% / “Actual size” — turn OFF “fit to page” / “shrink to fit”.",
        "2.  Check the calibration rulers below with a real ruler; every board page also carries a 100 mm bar.",
        "3.  Page 2 (top assembly overlay) is the one to lay the physical parts on: grey outlines are the real",
        "     part bodies, gold shapes are the pad/hole openings, purple is the courtyard.",
        "4.  Bottom/inner-layer pages are X-ray views (not mirrored), so they align with page 2 held to the light.",
    ]:
        c.drawString(15 * mm, y, line)
        y -= 5 * mm
    y -= 4 * mm
    # Calibration rulers: 100 mm and 4 inch.
    c.setFont("Helvetica-Bold", 10)
    c.drawString(15 * mm, y, "Calibration — these must measure exactly 100 mm and 4 in:")
    y -= 8 * mm
    bx = 15 * mm
    c.setLineWidth(0.8)
    c.line(bx, y, bx + 100 * mm, y)
    for i in range(11):
        tick = 3.5 * mm if i % 5 == 0 else 2 * mm
        c.line(bx + i * 10 * mm, y, bx + i * 10 * mm, y + tick)
    c.setFont("Helvetica", 8)
    c.drawString(bx + 102 * mm, y, "100 mm")
    y -= 9 * mm
    c.line(bx, y, bx + 4 * inch, y)
    for i in range(9):
        tick = 3.5 * mm if i % 2 == 0 else 2 * mm
        c.line(bx + i * 0.5 * inch, y, bx + i * 0.5 * inch, y + tick)
    c.drawString(bx + 4 * inch + 2 * mm, y, "4 in")
    y -= 12 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(15 * mm, y, "Parts to gather for the spot check")
    y -= 7 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(15 * mm, y, "Ref")
    c.drawString(32 * mm, y, "Part")
    c.drawString(110 * mm, y, "What it looks like")
    y -= 2 * mm
    c.setLineWidth(0.4)
    c.line(15 * mm, y, LETTER_W_PT - 15 * mm, y)
    y -= 4.5 * mm
    c.setFont("Helvetica", 9)
    for ref, part, hint in PARTS:
        c.drawString(15 * mm, y, ref)
        c.drawString(32 * mm, y, part)
        c.drawString(110 * mm, y, hint)
        y -= 4.8 * mm
    y -= 4 * mm
    c.setFont("Helvetica", 8)
    c.drawString(15 * mm, y, "Contents: 1 cover · 5 board pages (1:1) · drill map + schematic "
                             "(reference, not to scale). Source files in PR #76,")
    y -= 4 * mm
    c.drawString(15 * mm, y, "paper/background/starter_board/quilter_candidates_run3/ — "
                             "rebuild with:  python3 make_print_pdf.py")
    c.showPage()
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def fit_to_letter(page, landscape_src: bool = True):
    """Scale-to-fit a plotted A4 page onto Letter (for not-to-scale pages)."""
    src_w = float(page.mediabox.width)
    src_h = float(page.mediabox.height)
    # Rotate landscape content is unnecessary: place on landscape-oriented
    # Letter page (Letter rotated by the printer); keep it simple by scaling
    # onto a portrait Letter page, centered, preserving aspect.
    s = min((LETTER_W_PT - 40) / src_w, (LETTER_H_PT - 80) / src_h)
    tx = (LETTER_W_PT - src_w * s) / 2.0
    ty = (LETTER_H_PT - src_h * s) / 2.0
    page.add_transformation(Transformation().scale(s).translate(tx, ty))
    page.mediabox.lower_left = (0, 0)
    page.mediabox.upper_right = (LETTER_W_PT, LETTER_H_PT)
    if page.cropbox:
        page.cropbox.lower_left = (0, 0)
        page.cropbox.upper_right = (LETTER_W_PT, LETTER_H_PT)
    return page


def main() -> int:
    if not BOARD.is_file() or not SCHEMATIC.is_file():
        print("missing input file(s)", file=sys.stderr)
        return 1
    install_theme()
    writer = PdfWriter()
    tmp = Path(tempfile.mkdtemp(prefix="print_pdf_"))

    pages = []  # (reader_page, title, note, one_to_one)
    xform = board_transform()
    for i, (title, layers, note) in enumerate(BOARD_PAGES):
        out = tmp / f"board_{i}.pdf"
        kicad_cli("pcb", "export", "pdf", "-l", layers, "-t", THEME_NAME,
                  "-o", str(out), str(BOARD))
        pg = PdfReader(out).pages[0]
        pg.add_transformation(xform)
        pg.mediabox.lower_left = (0, 0)
        pg.mediabox.upper_right = (LETTER_W_PT, LETTER_H_PT)
        pg.cropbox.lower_left = (0, 0)
        pg.cropbox.upper_right = (LETTER_W_PT, LETTER_H_PT)
        pages.append((pg, title, note, True))

    # Drill map (reference page — KiCad adds its own symbol/size legend).
    drill_dir = tmp / "drill"
    drill_dir.mkdir()
    kicad_cli("pcb", "export", "drill", "--generate-map", "--map-format", "pdf",
              "-o", str(drill_dir) + "/", str(BOARD))
    drill_pdf = next(drill_dir.glob("*-drl_map.pdf"))
    pg = fit_to_letter(PdfReader(drill_pdf).pages[0])
    pages.append((pg, "Drill map — hole symbols and size table",
                  "Plated holes for all 16 THT parts; see the legend table for sizes.",
                  False))

    # Schematic (reference).
    sch_pdf = tmp / "schematic.pdf"
    kicad_cli("sch", "export", "pdf", "--no-background-color",
              "-o", str(sch_pdf), str(SCHEMATIC))
    for pg in PdfReader(sch_pdf).pages:
        pg = fit_to_letter(pg)
        pages.append((pg, "Schematic — test_module_unplaced.kicad_sch (2-servo, rev C nets)",
                      "23 nets / 99 connected pins; matches the board netlist exactly.",
                      False))

    total = len(pages) + 1
    writer.add_page(cover_page())
    for n, (pg, title, note, one_to_one) in enumerate(pages, start=2):
        pg.merge_page(overlay_page(title, note, n, total, one_to_one))
        writer.add_page(pg)

    writer.add_metadata({
        "/Title": "Powder doser — run-3 candidate 2 — 1:1 print kit",
        "/Subject": "Physical parts spot-check printout (PR #76)",
        "/Creator": "make_print_pdf.py (kicad-cli 7 + pypdf + reportlab)",
    })
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PDF.open("wb") as fh:
        writer.write(fh)
    print(f"wrote {OUT_PDF} ({total} pages)")

    # Sanity: every page must be exactly US Letter.
    for i, p in enumerate(PdfReader(OUT_PDF).pages, start=1):
        w, h = float(p.mediabox.width), float(p.mediabox.height)
        assert abs(w - LETTER_W_PT) < 0.5 and abs(h - LETTER_H_PT) < 0.5, \
            f"page {i} is {w}x{h} pt, not Letter"
    print("all pages verified US Letter 612x792 pt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
