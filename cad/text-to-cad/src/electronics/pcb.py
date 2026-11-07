"""POWDER_DOSER_V2 bare PCB, built directly from the team's Gerber/drill set.

Input: hardware/PCBs/POWDER_DOSER_V2.zip (EasyEDA Pro 3.2.149 export,
2026-09-29), read in place by pcb_gerber.py.

Frame: origin at the board's lower-left outline corner, X along the 101.6 mm
edge, Y along the 76.2 mm edge, Z up; FR-4 from z = 0 to z = 1.6.

Bodies (separately coloured):
  fr4         1.6 mm board from the GKO outline; all 137 holes (PTH, NPTH,
              vias, barrel-jack slots) drilled as true cylinders / slots
  pads_top    exposed copper: one annular sheet per GTS mask opening, shaped
              like the GTL pad aperture under it (R/C/O) minus its drill,
              0.03 mm above the top face
  copper_top  GTL tracks + pours under the solder mask (lighter green), sheet
              0.015 mm above the top face, simplified to 0.25 mm
  silk_top    GTO component outlines (rectangles, circles, cap polarity
              marks), sheet 0.045 mm above the top face
Left out to keep the STEP small (the first, complete build was 130 MB, an
edge costs about 1 kB): silkscreen text, bottom copper/pads (GBL/GBS) and the
empty bottom silkscreen.  The full artwork, text included, is compared with
this model in renders/electronics/pcb_vs_gerber.png.
"""
from __future__ import annotations

from cadgen import build123d as bd
from cadgen import srgb, step

import pcb_gerber as G
from pcb_layout import BOARD_T

MASK_GREEN = "#1F6F3A"
MASK_OVER_COPPER = "#3E9C57"
PAD_FINISH = "#D9B45A"       # gold-coloured exposed copper; finish not in the Gerbers
SILK_WHITE = "#F4F4F0"

Z_CU = 0.015            # sheet offsets above the top face
Z_PAD = 0.03
Z_SILK = 0.045
CU_SIMPLIFY = 0.25
SILK_SIMPLIFY = 0.03


def _pad_face(ap: G.Aperture, drill: G.Drill | None, x: float, y: float, z: float) -> bd.Face:
    """Annular pad face at (x, y, z), built from wires in absolute coordinates
    (moved sketch faces lose their colour on export)."""
    from shapely.geometry import LineString

    plane = bd.Plane((x, y, z))
    k, p = ap.kind, ap.params

    def poly_wire(geom):
        pts = list(geom.exterior.coords)[:-1]
        return bd.Wire.make_polygon([bd.Vector(px, py, z) for px, py in pts], close=True)

    if k == "C":
        outer = bd.Wire.make_circle(p[0] / 2, plane)
    elif k == "R":
        outer = bd.Wire.make_rect(p[0], p[1], plane)
    elif k == "O":
        w, h = p[0], p[1]
        r = min(w, h) / 2
        seg = (LineString([(x - w / 2 + r, y), (x + w / 2 - r, y)]) if w >= h
               else LineString([(x, y - h / 2 + r), (x, y + h / 2 - r)]))
        outer = poly_wire(seg.buffer(r, quad_segs=4))
    else:
        raise ValueError(k)
    if drill is None:
        return bd.Face(outer)
    if drill.is_slot:
        hole = poly_wire(LineString([(drill.x - 0, drill.y), (drill.x2, drill.y2)]).buffer(
            drill.dia / 2, quad_segs=4))
    else:
        hole = bd.Wire.make_circle(drill.dia / 2, plane)
    return bd.Face(outer, [hole])


def _drill_tool(d: G.Drill, cx: float, cy: float, z0: float, height: float) -> bd.Shape:
    if d.is_slot:
        import math
        dx, dy = d.x2 - d.x, d.y2 - d.y
        sep = math.hypot(dx, dy)
        slot = bd.SlotCenterToCenter(sep, d.dia, rotation=math.degrees(math.atan2(dy, dx)))
        tool = bd.extrude(slot, amount=height)
    else:
        tool = bd.Cylinder(d.dia / 2, height, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    return tool.moved(bd.Location((cx, cy, z0)))


def _sheet(faces, label: str, colour: str):
    for f in faces:             # leaf colour: a group colour does not reach every face
        f.color = srgb(colour)
    comp = bd.Compound(faces)
    comp.label = label
    comp.color = srgb(colour)
    return comp


def build_pcb() -> bd.Shape:
    ox, oy = G.board_origin()
    to_b = lambda g: G.to_board(g, (ox, oy))  # noqa: E731

    layers = {k: G.parse_gerber(G.read_zip_text(f), k) for k, f in G.LAYER_FILES.items()}
    drills = G.drills()
    centres = [(G.drill_centre(d), d) for d in drills]

    # --- FR-4 core with every hole drilled (true cylinders / slots) ---------
    minx, miny, maxx, maxy = G.outline_polygon().bounds
    core = bd.Box(maxx - minx, maxy - miny, BOARD_T, align=(bd.Align.MIN,) * 3)
    tools = [_drill_tool(d, c[0] - ox, c[1] - oy, -1.0, BOARD_T + 2.0) for c, d in centres]
    fr4 = core.cut(bd.Compound(tools))
    fr4.label = "fr4"
    fr4.color = srgb(MASK_GREEN)
    parts = [fr4]

    from shapely.ops import unary_union
    hole_union = to_b(unary_union([G.drill_geometry(d) for d in drills]))

    # exposed pads: one per top mask opening, copper aperture at the same spot
    cu_flash = {(round(x, 3), round(y, 3)): ap for x, y, ap in layers["top_copper"].flash_list}
    pads = []
    for x, y, _mask_ap in layers["top_mask"].flash_list:
        ap = cu_flash.get((round(x, 3), round(y, 3)))
        if ap is None:
            continue
        near = [d for c, d in centres if abs(c[0] - x) < 0.01 and abs(c[1] - y) < 0.01]
        d = near[0] if near else None
        if d is not None and d.is_slot:          # slot ends in the board frame
            d = G.Drill(d.x - ox, d.y - oy, d.dia, d.plated, d.via, d.x2 - ox, d.y2 - oy)
        pads.append(_pad_face(ap, d, x - ox, y - oy, BOARD_T + Z_PAD))
    parts.append(_sheet(pads, "pads_top", PAD_FINISH))

    # copper under the mask: tracks + pours minus mask openings and holes
    covered = to_b(layers["top_copper"].all).difference(
        to_b(layers["top_mask"].all)).difference(hole_union)
    parts.append(_sheet(G.face_polygons(covered, BOARD_T + Z_CU, CU_SIMPLIFY),
                        "copper_top", MASK_OVER_COPPER))

    # silkscreen outlines (EasyEDA "Text" objects left out, see docstring)
    silk = to_b(G.strokes_geometry(layers["top_silk"])).difference(hole_union)
    parts.append(_sheet(G.face_polygons(silk, BOARD_T + Z_SILK, SILK_SIMPLIFY),
                        "silk_top", SILK_WHITE))

    return bd.Compound(children=parts, label="powder_doser_v2_pcb")


@step(out="../../STEP/electronics/pcb.step")
def pcb():
    return build_pcb()


if __name__ == "__main__":
    pcb()
