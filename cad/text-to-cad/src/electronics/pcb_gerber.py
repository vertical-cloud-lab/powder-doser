"""Minimal RS-274X / Excellon reader for the POWDER_DOSER_V2 Gerber set.

Plain helper module (not a model).  It covers exactly what EasyEDA Pro's
"one-click" Gerber generator emits for this board:

* ``%FSLAX45Y45*%`` / ``%MOMM*%`` coordinates (leading zeros omitted, 5 decimals)
* apertures ``C``, ``R``, ``O`` and the ``RoundRect`` macro (mask layers)
* ``G01`` lines, ``G02``/``G03`` arcs (``G75`` multi-quadrant, I/J offsets)
* ``D01`` draw, ``D02`` move, ``D03`` flash, ``G36``/``G37`` regions
* Excellon drills with ``T`` tools, decimal coordinates and ``G85`` slots

Every layer is returned as a single shapely geometry in Gerber coordinates
(millimetres).  ``board_frame()`` shifts it to the board frame used by the CAD
models (origin at the lower-left outline corner).
"""
from __future__ import annotations

import json
import math
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

ZIP_PATH = (Path(__file__).resolve().parents[4] / "hardware" / "PCBs"
            / "POWDER_DOSER_V2.zip")

LAYER_FILES = {
    "outline": "Gerber_BoardOutlineLayer.GKO",
    "top_copper": "Gerber_TopLayer.GTL",
    "bottom_copper": "Gerber_BottomLayer.GBL",
    "top_silk": "Gerber_TopSilkscreenLayer.GTO",
    "bottom_silk": "Gerber_BottomSilkscreenLayer.GBO",
    "top_mask": "Gerber_TopSolderMaskLayer.GTS",
    "bottom_mask": "Gerber_BottomSolderMaskLayer.GBS",
    "document": "Gerber_DocumentLayer.GDL",
}
DRILL_FILES = {
    "pth": "Drill_PTH_Through.DRL",
    "npth": "Drill_NPTH_Through.DRL",
    "via": "Drill_PTH_Through_Via.DRL",
}
PROBE_FILE = "FlyingProbeTesting.json"

ARC_SEG_MM = 0.15        # chord length used to flatten arcs
QUAD_SEGS = 4            # shapely buffer segments per quarter circle


def read_zip_text(name: str, zip_path: Path = ZIP_PATH) -> str:
    with zipfile.ZipFile(zip_path) as zf:
        return zf.read(name).decode("utf-8", "replace")


# --------------------------------------------------------------------------
# apertures
# --------------------------------------------------------------------------
@dataclass
class Aperture:
    kind: str                 # C, R, O, RoundRect
    params: tuple[float, ...]

    @property
    def stroke_width(self) -> float:
        if self.kind == "C":
            return self.params[0]
        return min(self.params[:2]) if len(self.params) >= 2 else self.params[0]

    def flash(self, x: float, y: float):
        k, p = self.kind, self.params
        if k == "C":
            return Point(x, y).buffer(p[0] / 2, quad_segs=QUAD_SEGS * 2)
        if k == "R":
            return box(x - p[0] / 2, y - p[1] / 2, x + p[0] / 2, y + p[1] / 2)
        if k == "O":
            w, h = p[0], p[1]
            r = min(w, h) / 2
            if w >= h:
                seg = LineString([(x - w / 2 + r, y), (x + w / 2 - r, y)])
            else:
                seg = LineString([(x, y - h / 2 + r), (x, y + h / 2 - r)])
            return seg.buffer(r, quad_segs=QUAD_SEGS * 2)
        if k == "RoundRect":
            # EasyEDA macro: $1 corner-circle diameter; corners at
            # ($2,$3), ($4,$5) and their point reflections
            rd, a, b, c, d = p[:5]
            corners = [(x + a, y + b), (x + c, y + d), (x - a, y - b), (x - c, y - d)]
            poly = Polygon(corners).convex_hull
            if poly.area < 1e-9:             # degenerate listing: use bbox
                xs = [c[0] for c in corners]
                ys = [c[1] for c in corners]
                poly = box(min(xs), min(ys), max(xs), max(ys))
            return poly.buffer(rd / 2, quad_segs=QUAD_SEGS)
        raise ValueError(f"unsupported aperture {k}")


_AD_RE = re.compile(r"%ADD(\d+)([A-Za-z_]+),?([^*]*)\*%")
_COORD_RE = re.compile(r"([XYIJ])(-?\d+)")


def _arc_points(x0, y0, x1, y1, i, j, cw: bool):
    cx, cy = x0 + i, y0 + j
    r = math.hypot(x0 - cx, y0 - cy)
    a0 = math.atan2(y0 - cy, x0 - cx)
    a1 = math.atan2(y1 - cy, x1 - cx)
    if cw:
        while a1 >= a0:
            a1 -= 2 * math.pi
    else:
        while a1 <= a0:
            a1 += 2 * math.pi
    if abs(x0 - x1) < 1e-9 and abs(y0 - y1) < 1e-9:   # full circle
        a1 = a0 + (-2 * math.pi if cw else 2 * math.pi)
    n = max(4, int(abs(a1 - a0) * r / ARC_SEG_MM) + 1)
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n),
             cy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(1, n + 1)]


@dataclass
class GerberLayer:
    name: str
    tracks: object        # union of stroked D01 segments
    flashes: object       # union of D03 flashes
    regions: object       # union of G36/G37 regions
    strokes: list         # [(LineString, width, block)] raw stroked paths; block is
                          # the EasyEDA object group ("Text", "Rect", ...) or ""

    flash_list: list      # [(x, y, Aperture)]

    @property
    def all(self):
        return unary_union([g for g in (self.tracks, self.flashes, self.regions)
                            if g is not None and not g.is_empty])


def parse_gerber(text: str, name: str = "") -> GerberLayer:
    scale = 1e-5
    fs = re.search(r"%FSLAX(\d)(\d)Y(\d)(\d)\*%", text)
    if fs:
        scale = 10.0 ** (-int(fs.group(2)))
    apertures: dict[int, Aperture] = {}
    for m in _AD_RE.finditer(text):
        code, kind, params = int(m.group(1)), m.group(2), m.group(3)
        vals = tuple(float(v) for v in params.split("X") if v != "")
        apertures[code] = Aperture(kind, vals)

    # strip parameter blocks, then walk the word stream
    body = re.sub(r"%[^%]*%", "", text)
    words = [w.strip() for w in body.replace("\n", "").split("*")]

    x = y = 0.0
    interp = "G01"
    cur_ap: Aperture | None = None
    in_region = False
    region_pts: list = []
    regions, track_geoms, flash_geoms = [], [], []
    strokes, flash_list = [], []
    path: list = []          # current stroked path (for strokes list)
    block = ""

    def end_path():
        nonlocal path
        if len(path) >= 2 and cur_ap is not None:
            strokes.append((LineString(path), cur_ap.stroke_width, block))
        path = []

    def close_region():
        nonlocal region_pts
        if len(region_pts) >= 3:
            poly = Polygon(region_pts)
            if not poly.is_valid:
                poly = poly.buffer(0)
            regions.append(poly)
        region_pts = []

    for w in words:
        if w.startswith("G04"):
            m_blk = re.match(r"G04 (\w+) (Start|End)", w)
            if m_blk:
                end_path()
                block = m_blk.group(1) if m_blk.group(2) == "Start" else ""
            continue
        if not w:
            continue
        if w.startswith("M02"):
            break
        g = re.match(r"G0?(\d+)", w)
        if g:
            gnum = int(g.group(1))
            if gnum in (1, 2, 3):
                interp = f"G0{gnum}"
            elif gnum == 36:
                in_region = True
                region_pts = []
                continue
            elif gnum == 37:
                close_region()
                in_region = False
                continue
            elif gnum == 54:
                pass
            elif gnum in (74, 75):
                continue
        dsel = re.search(r"D(\d+)$", w)
        dcode = int(dsel.group(1)) if dsel else None
        if dcode is not None and dcode >= 10:
            end_path()
            cur_ap = apertures[dcode]
            continue
        coords = dict((k, int(v) * scale) for k, v in _COORD_RE.findall(w))
        if not coords and dcode is None:
            continue
        nx, ny = coords.get("X", x), coords.get("Y", y)
        if dcode is None:
            dcode = 1          # modal D01 (not emitted by this generator)
        if dcode == 2:
            if in_region:
                close_region()
                region_pts = [(nx, ny)]
            else:
                end_path()
                path = [(nx, ny)]
        elif dcode == 1:
            if interp == "G01":
                seg = [(nx, ny)]
            else:
                seg = _arc_points(x, y, nx, ny, coords.get("I", 0.0),
                                  coords.get("J", 0.0), interp == "G02")
            if in_region:
                if not region_pts:
                    region_pts = [(x, y)]
                region_pts.extend(seg)
            else:
                if not path:
                    path = [(x, y)]
                path.extend(seg)
        elif dcode == 3:
            end_path()
            if cur_ap is not None:
                flash_list.append((nx, ny, cur_ap))
                flash_geoms.append(cur_ap.flash(nx, ny))
        x, y = nx, ny
    end_path()

    for line, width, _blk in strokes:
        if line.length < 1e-9:
            track_geoms.append(Point(line.coords[0]).buffer(width / 2, quad_segs=QUAD_SEGS))
        else:
            track_geoms.append(line.buffer(width / 2, quad_segs=QUAD_SEGS))
    return GerberLayer(
        name=name,
        tracks=unary_union(track_geoms) if track_geoms else Polygon(),
        flashes=unary_union(flash_geoms) if flash_geoms else Polygon(),
        regions=unary_union(regions) if regions else Polygon(),
        strokes=strokes,
        flash_list=flash_list,
    )


# --------------------------------------------------------------------------
# Excellon
# --------------------------------------------------------------------------
@dataclass
class Drill:
    x: float
    y: float
    dia: float
    plated: bool
    via: bool = False
    x2: float | None = None     # slot end (G85), else None
    y2: float | None = None

    @property
    def is_slot(self) -> bool:
        return self.x2 is not None


def parse_excellon(text: str, plated: bool, via: bool = False) -> list[Drill]:
    tools: dict[str, float] = {}
    out: list[Drill] = []
    cur = None
    for raw in text.splitlines():
        line = raw.strip()
        m = re.match(r"^T(\d+)C([\d.]+)", line)
        if m:
            tools[m.group(1)] = float(m.group(2))
            continue
        m = re.match(r"^T(\d+)$", line)
        if m:
            cur = tools[m.group(1)]
            continue
        m = re.match(r"^X(-?[\d.]+)Y(-?[\d.]+)(?:G85X(-?[\d.]+)Y(-?[\d.]+))?$", line)
        if m and cur is not None:
            x, y = float(m.group(1)), float(m.group(2))
            if m.group(3):
                out.append(Drill(x, y, cur, plated, via, float(m.group(3)), float(m.group(4))))
            else:
                out.append(Drill(x, y, cur, plated, via))
    return out


def drills(zip_path: Path = ZIP_PATH) -> list[Drill]:
    """All holes; vias are listed in both PTH files, so de-duplicate them."""
    via = parse_excellon(read_zip_text(DRILL_FILES["via"], zip_path), True, True)
    pth = parse_excellon(read_zip_text(DRILL_FILES["pth"], zip_path), True)
    npth = parse_excellon(read_zip_text(DRILL_FILES["npth"], zip_path), False)
    via_keys = {(round(d.x, 4), round(d.y, 4)) for d in via}
    pth = [d for d in pth if (round(d.x, 4), round(d.y, 4)) not in via_keys]
    return pth + via + npth


def drill_geometry(d: Drill):
    if d.is_slot:
        return LineString([(d.x, d.y), (d.x2, d.y2)]).buffer(d.dia / 2, quad_segs=QUAD_SEGS * 2)
    return Point(d.x, d.y).buffer(d.dia / 2, quad_segs=QUAD_SEGS * 2)


# --------------------------------------------------------------------------
# flying-probe netlist (component names, centres, pins, nets)
# --------------------------------------------------------------------------
MIL = 0.0254


def probe_data(zip_path: Path = ZIP_PATH) -> tuple[list[dict], list[dict]]:
    data = json.loads(read_zip_text(PROBE_FILE, zip_path))
    comps = []
    for row in data["components"]["rows"]:
        no, name, layer, x, y, ang = row
        if re.fullmatch(r"PAD\d+", name):
            continue
        comps.append({"name": name, "x": x * MIL, "y": y * MIL, "angle": ang,
                      "layer": layer})
    pins, seen = [], set()
    for row in data["pins"]["rows"]:
        (_no, pname, px, py, layer, ptype, net, _nt, shape, sx, sy,
         hole, hole_len, pang) = row
        key = (pname, px, py)
        if key in seen or re.match(r"PAD\d+_", pname):
            continue
        seen.add(key)
        comps_name, pin_no = pname.rsplit("_", 1)
        pins.append({"component": comps_name, "pin": int(pin_no), "x": px * MIL,
                     "y": py * MIL, "net": net, "shape": shape,
                     "pad": (sx * MIL, sy * MIL), "hole": hole * MIL,
                     "hole_len": hole_len * MIL, "pad_angle": pang})
    return comps, pins


def outline_polygon(zip_path: Path = ZIP_PATH) -> Polygon:
    layer = parse_gerber(read_zip_text(LAYER_FILES["outline"], zip_path), "outline")
    pts = []
    for line, _w, _b in layer.strokes:
        pts.extend(line.coords)
    poly = Polygon(pts).convex_hull     # the outline is a plain rectangle
    return poly


def board_origin(zip_path: Path = ZIP_PATH) -> tuple[float, float]:
    minx, miny, _maxx, _maxy = outline_polygon(zip_path).bounds
    return minx, miny


def to_board(geom, origin):
    return affinity.translate(geom, -origin[0], -origin[1])


# --------------------------------------------------------------------------
# shapely -> build123d
# --------------------------------------------------------------------------
def polygons(geom) -> list:
    """Flatten any shapely geometry into its Polygon parts."""
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    out = []
    for g in getattr(geom, "geoms", []):
        out.extend(polygons(g))
    return out


def extrude_polygons(geom, z0: float, height: float, simplify: float = 0.01):
    """Extrude every polygon of a shapely geometry from z0 by height.

    Returns a list of build123d Solids (empty polygons skipped)."""
    from cadgen import build123d as bd

    solids = []
    for poly in polygons(geom):
        if simplify:
            poly = poly.simplify(simplify, preserve_topology=True)
        if poly.is_empty or poly.area < 1e-4:
            continue

        def wire(ring):
            pts = list(ring.coords)[:-1]
            return bd.Wire.make_polygon([bd.Vector(x, y, z0) for x, y in pts], close=True)

        try:
            face = bd.Face(wire(poly.exterior), [wire(r) for r in poly.interiors
                                                 if len(r.coords) > 3])
            solids.append(bd.Solid.extrude(face, bd.Vector(0, 0, height)))
        except Exception:      # degenerate sliver: skip rather than fail the board
            continue
    return solids


def face_polygons(geom, z: float, simplify: float = 0.03, flip: bool = False):
    """Planar build123d Faces (zero-thickness sheets) for a shapely geometry.

    Used for the cosmetic copper-under-mask and silkscreen layers: a sheet has
    no side faces, which keeps the STEP small and the mesh fast."""
    from cadgen import build123d as bd

    faces = []
    for poly in polygons(geom):
        if simplify:
            poly = poly.simplify(simplify, preserve_topology=True)
        if poly.is_empty or poly.area < 1e-4:
            continue

        def wire(ring):
            pts = list(ring.coords)[:-1]
            return bd.Wire.make_polygon([bd.Vector(x, y, z) for x, y in pts], close=True)

        try:
            face = bd.Face(wire(poly.exterior), [wire(r) for r in poly.interiors
                                                 if len(r.coords) > 3])
        except Exception:
            continue
        if flip:
            face = -face
        faces.append(face)
    return faces


def drill_centre(d: Drill) -> tuple[float, float]:
    if d.is_slot:
        return ((d.x + d.x2) / 2, (d.y + d.y2) / 2)
    return (d.x, d.y)


def strokes_geometry(layer: GerberLayer, skip_blocks=("Text",), quad_segs: int = 2):
    """Union of a layer's stroked paths (square caps, mitred joins: few
    vertices) excluding the given EasyEDA object blocks, plus its regions."""
    geoms = []
    for line, width, blk in layer.strokes:
        if blk in skip_blocks:
            continue
        if line.length < 1e-9:
            geoms.append(Point(line.coords[0]).buffer(width / 2, quad_segs=quad_segs))
        else:
            geoms.append(line.buffer(width / 2, quad_segs=quad_segs, cap_style=3, join_style=2))
    if layer.regions is not None and not layer.regions.is_empty:
        geoms.append(layer.regions)
    return unary_union(geoms) if geoms else Polygon()
