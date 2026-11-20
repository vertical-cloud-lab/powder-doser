"""Animated shop processes for the parts we machine or modify ourselves (PR #185, issue #128).

Every workpiece is built from the designs' own CAD (each design's parts.py / layout.shape), so the last
frame of each process is the part we ship. Bought parts that the shop modifies (the sprockets, the steel
pinion) start from the bought part's geometry and lose material frame by frame. Plates start from the
blank and lose the CAD's own holes one at a time (blank minus part, split into its solids).

    xvfb-run -a python shop_anim.py all            # every process, one after another
    xvfb-run -a python shop_anim.py pat_plates v2_plates ...
    python shop_anim.py sheet                      # contact sheet from anim/*_key.png

Both designs have modules called params/parts/layout, so design() purges them from sys.modules and
imports the other design's copies; each animation pulls everything it needs before switching.
"""
from __future__ import annotations

import importlib
import math
import sys
import textwrap
import time
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import imageio.v2 as imageio
import matplotlib
import numpy as np
import pyvista as pv
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
CAD = HERE.parent
OUT = HERE / "anim"
OUT.mkdir(exist_ok=True)

W, H, SS = 900, 506, 2
_FONTS = Path(matplotlib.get_data_path()) / "fonts" / "ttf"


def font(px: int, style: str = "") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(_FONTS / f"DejaVuSans{style}.ttf"), px)


F_TITLE, F_PART, F_CAP, F_NOTE, F_LAB = font(21, "-Bold"), font(14), font(15), font(14, "-Oblique"), font(13)
INK, INK2 = (25, 30, 38), (70, 78, 90)

ALU = "#c9ced5"
STEEL = "#a7afb8"
DARKSTEEL = "#56616d"
TOOL = "#3d4a57"
CARBIDE = "#c9a03c"
CHUCK = "#6d737b"
JAW = "#98a0a8"
SOFTJAW = "#d7dbe0"
SECTION = "#e4a98d"
TABLE = "#6b7680"
SLAT = "#8d969e"
BENCH = "#cfae7d"
KERF = "#c0392b"
BRASS = "#c8a24a"
PETG_BLUE = "#3b5bd6"
BLACKOX = "#2f3338"
BEARING = "#b9c0c8"

# ---------------------------------------------------------------------------------------------------------------
# Designs
# ---------------------------------------------------------------------------------------------------------------
_MODS = ("params", "parts", "layout", "kinematics", "bom", "docs", "step_io", "render", "build", "check_interference")
_LOADED: dict[str, SimpleNamespace] = {}


def design(name: str) -> SimpleNamespace:
    """Import one design's params/parts/layout (purging the other design's modules of the same names)."""
    if name in _LOADED:
        return _LOADED[name]
    d = str(CAD / name)
    for attempt in range(4):
        for m in _MODS:
            sys.modules.pop(m, None)
        sys.path.insert(0, d)
        try:
            L = importlib.import_module("layout")
            ns = SimpleNamespace(P=sys.modules["params"], PT=sys.modules["parts"], L=L, name=name,
                                 step_io=sys.modules.get("step_io"))
            break
        except Exception as e:  # another agent may be mid-edit: wait and retry
            print(f"import of {name} failed ({e!r}); retrying in 60 s", flush=True)
            time.sleep(60)
        finally:
            sys.path.remove(d)
    else:
        raise RuntimeError(f"cannot import {name}")
    _LOADED[name] = ns
    return ns


def solid(x) -> cq.Shape:
    if isinstance(x, cq.Workplane):
        vals = [v for v in x.vals() if isinstance(v, cq.Shape)]
        return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)
    return x


# ---------------------------------------------------------------------------------------------------------------
# CadQuery -> PyVista
# ---------------------------------------------------------------------------------------------------------------
class Mesh:
    """Body mesh + section-face mesh + feature edges of one shape; move/turn copies all three."""

    def __init__(self, body, section=None, edges=None):
        self.body, self.section, self.edges = body, section, edges

    def _map(self, f):
        return Mesh(*(f(m) if m is not None else None for m in (self.body, self.section, self.edges)))

    def move(self, v):
        return self._map(lambda m: m.translate(v, inplace=False))

    def rot(self, axis: str, ang: float, point=(0, 0, 0)):
        if abs(ang) < 1e-9:
            return self
        f = {"x": "rotate_x", "y": "rotate_y", "z": "rotate_z"}[axis]
        return self._map(lambda m: getattr(m, f)(ang, point=point, inplace=False))


def _poly(shape, tol, ang):
    v, t = shape.tessellate(tol, ang)
    if not t:
        return None
    pts = np.array([p.toTuple() for p in v], float)
    tri = np.asarray(t, int)
    return pv.PolyData(pts, np.column_stack([np.full(len(tri), 3), tri]).ravel()).clean()


def mesh(shape, tol=0.05, ang=0.25, section_y=None, edge_angle=32.0) -> Mesh:
    """Tessellate; faces lying on the plane y = section_y (a half-section's cut face) go to their own mesh."""
    s = solid(shape)
    if section_y is None:
        body, sec = _poly(s, tol, ang), None
    else:
        keep, cut = [], []
        for f in s.Faces():
            c = f.Center()
            bb = f.BoundingBox()
            (cut if (bb.ylen < 1e-4 and abs(c.y - section_y) < 1e-3) else keep).append(f)
        body = _poly(cq.Compound.makeCompound(keep), tol, ang) if keep else None
        sec = _poly(cq.Compound.makeCompound(cut), tol, ang) if cut else None
    allm = body if sec is None else (sec if body is None else body.merge(sec).clean())
    edges = allm.extract_feature_edges(edge_angle, boundary_edges=False, feature_edges=True, manifold_edges=False,
                                       non_manifold_edges=False) if allm is not None else None
    return Mesh(body, sec, edges)


_CACHE: dict = {}


def cached(key, make, **kw) -> Mesh:
    if key not in _CACHE:
        _CACHE[key] = mesh(make(), **kw)
    return _CACHE[key]


def halve(shape, keep_pos_y=True, y=0.0):
    """Cut away the near (-y) half so the inside shows; returns the shape and the section plane."""
    s = solid(shape)
    bb = s.BoundingBox()
    big = 4 * max(bb.xlen, bb.ylen, bb.zlen) + 10
    box = cq.Solid.makeBox(big, big, big, cq.Vector(bb.center.x - big / 2, y - big if keep_pos_y else y,
                                                      bb.center.z - big / 2))
    return s.cut(box)


def cyl_x(r, x0, x1, y=0.0, z=0.0):
    """Solid cylinder along x from x0 to x1."""
    return cq.Solid.makeCylinder(r, x1 - x0, cq.Vector(x0, y, z), cq.Vector(1, 0, 0))


def cyl_z(r, z0, z1, x=0.0, y=0.0):
    return cq.Solid.makeCylinder(r, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def turned(profile, x0=0.0):
    """Revolve an (x, r) half-profile about the x axis (x along the lathe axis)."""
    pts = []
    for x, r in profile:                    # drop repeated points: a zero-length edge breaks the polyline
        if not pts or abs(x0 + x - pts[-1][0]) > 1e-6 or abs(r - pts[-1][1]) > 1e-6:
            pts.append((x0 + x, r))
    if abs(pts[0][0] - pts[-1][0]) < 1e-6 and abs(pts[0][1] - pts[-1][1]) < 1e-6:
        pts.pop()
    w = cq.Workplane("XY").polyline(pts).close()
    return solid(w.revolve(360, (0, 0, 0), (1, 0, 0)))


def flat(shape):
    """Lay a plate flat: thinnest bounding-box axis -> z, longer in-plane side -> x, bottom on z = 0, centred."""
    s = solid(shape)
    bb = s.BoundingBox()
    dims = [bb.xlen, bb.ylen, bb.zlen]
    thin = int(np.argmin(dims))
    if thin == 0:
        s = s.rotate((0, 0, 0), (0, 1, 0), 90)
    elif thin == 1:
        s = s.rotate((0, 0, 0), (1, 0, 0), 90)
    bb = s.BoundingBox()
    if bb.ylen > bb.xlen:
        s = s.rotate((0, 0, 0), (0, 0, 1), 90)
    bb = s.BoundingBox()
    return s.translate(cq.Vector(-bb.center.x, -bb.center.y, -bb.zmin))


def blank_of(flat_part):
    """The flat part's outline with no holes (from its largest bottom face's outer wire)."""
    s = solid(flat_part)
    bb = s.BoundingBox()
    faces = [f for f in s.Faces() if f.geomType() == "PLANE" and abs(f.Center().z - bb.zmin) < 1e-4]
    f = max(faces, key=lambda f: f.Area())
    return cq.Solid.extrudeLinear(f.outerWire(), [], cq.Vector(0, 0, bb.zlen))


def tour(points, start=(-1e9, -1e9)):
    """Nearest-neighbour order of 2-D points."""
    left = list(range(len(points)))
    cur = np.array(start, float)
    order = []
    while left:
        k = min(left, key=lambda i: np.hypot(*(np.array(points[i]) - cur)))
        order.append(k)
        left.remove(k)
        cur = np.array(points[k], float)
    return order


def wire_points(wire, n=200):
    """Points along a wire (outline toolpath)."""
    pts = []
    for e in wire.Edges():
        k = max(2, int(n * e.Length() / wire.Length()))
        pts += [e.positionAt(t).toTuple() for t in np.linspace(0, 1, k)]
    return np.array(pts)


def helix_lines(x0, x1, r, pitch, n_per_turn=24):
    """Thread crest line on a cylinder along x (for showing threads that the CAD draws plain)."""
    if x1 - x0 < 1e-3:
        return None
    turns = (x1 - x0) / pitch
    t = np.linspace(0, turns * 2 * math.pi, max(4, int(turns * n_per_turn)))
    pts = np.column_stack([x0 + t / (2 * math.pi) * pitch, r * np.cos(t), r * np.sin(t)])
    return pv.lines_from_points(pts)


# ---------------------------------------------------------------------------------------------------------------
# Scene: off-screen PyVista + PIL captions
# ---------------------------------------------------------------------------------------------------------------
class Scene:
    def __init__(self, part: str, nsteps: int, persp=False):
        self.part, self.nsteps = part, nsteps
        self.pl = pv.Plotter(off_screen=True, window_size=(W * SS, H * SS), lighting="light_kit")
        self.pl.set_background("white")
        if not persp:
            self.pl.enable_parallel_projection()
        self.frames: list[np.ndarray] = []
        self.holds: list[float] = []
        self.key = None
        self.cam = None

    def clear(self):
        self.pl.clear()

    def add(self, m: Mesh, color, lw=1.0, opacity=1.0, edges=True, sec_color=SECTION, specular=0.3):
        if m.body is not None and m.body.n_cells:
            self.pl.add_mesh(m.body, color=color, smooth_shading=True, split_sharp_edges=True, feature_angle=32,
                             specular=specular, specular_power=20, ambient=0.18, diffuse=0.82, opacity=opacity)
        if m.section is not None and m.section.n_cells:
            self.pl.add_mesh(m.section, color=sec_color, ambient=0.35, diffuse=0.7, opacity=opacity)
        if edges and m.edges is not None and m.edges.n_points:
            self.pl.add_mesh(m.edges, color="#262b33", line_width=lw * SS, opacity=opacity)

    def lines(self, poly, color=KERF, lw=2.0):
        if poly is not None and poly.n_points:
            self.pl.add_mesh(poly, color=color, line_width=lw * SS)

    def camera(self, focal, direction, scale, up=(0, 0, 1)):
        d = np.array(direction, float)
        d /= np.linalg.norm(d)
        self.cam = (focal, d, scale, up)
        self.pl.camera_position = [tuple(np.array(focal) + 3000 * d), tuple(focal), up]
        self.pl.camera.parallel_scale = scale
        self.pl.camera.clipping_range = (1.0, 8000.0)

    def project(self, pts):
        ren = self.pl.renderer
        out = []
        for p in pts:
            ren.SetWorldPoint(float(p[0]), float(p[1]), float(p[2]), 1.0)
            ren.WorldToDisplay()
            x, y, _ = ren.GetDisplayPoint()
            out.append((x / SS, H - y / SS))
        return out

    def grab(self, step: int, title: str, caption: str = "", note: str | None = None, hold: float = 1.0,
             labels=(), key=False):
        if step != getattr(self, "_last_step", None):
            hold = max(hold, 14.0)          # first frame of a step: about 2.4 s to read the caption
            self._last_step = step
        img = self.pl.screenshot(return_img=True)
        anchors = self.project([lab[1] for lab in labels]) if labels else []
        im = Image.fromarray(img).resize((W, H), Image.LANCZOS).convert("RGB")
        d = ImageDraw.Draw(im, "RGBA")
        for (text, _, (tx, ty)), (x, y) in zip(labels, anchors):
            tx, ty = tx * W, ty * H
            d.line([(x, y), (tx, ty)], fill=INK2 + (255,), width=1)
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=INK2 + (255,), outline=(255, 255, 255, 255))
            lines = text.split("\n")
            tw = max(d.textlength(t_, font=F_LAB) for t_ in lines)
            th = 16 * len(lines)
            bx = tx if tx > x else tx - tw - 8
            bx = min(max(bx, 8), W - tw - 12)
            d.rounded_rectangle([bx - 3, ty - th / 2 - 3, bx + tw + 5, ty + th / 2 + 2], 4, fill=(255, 255, 255, 225))
            for i, t_ in enumerate(lines):
                d.text((bx + 1, ty - th / 2 + 16 * i), t_, font=F_LAB, fill=INK + (255,))
        d.text((16, 10), f"Step {step} of {self.nsteps}   {title}", font=F_TITLE, fill=INK)
        pw = d.textlength(self.part, font=F_PART)
        d.rounded_rectangle([W - pw - 24, 38, W - 8, 60], 5, fill=(255, 255, 255, 215))
        d.text((W - pw - 16, 41), self.part, font=F_PART, fill=INK2)
        if note:
            d.text((18, 40), note, font=F_NOTE, fill=INK2)
        if caption:
            lines = []
            for para in caption.split("\n"):
                lines += textwrap.wrap(para, 104)
            hbox = 8 + 19 * len(lines)
            d.rounded_rectangle([10, H - hbox - 10, W - 10, H - 8], 6, fill=(255, 255, 255, 228),
                                outline=(200, 205, 212, 255))
            for i, t_ in enumerate(lines):
                d.text((20, H - hbox - 5 + 19 * i), t_, font=F_CAP, fill=INK)
        self.frames.append(np.asarray(im))
        self.holds.append(hold)
        if key:
            self.key = len(self.frames) - 1

    def save(self, name: str, ms=170, tail_ms=3000, colours=128):
        imgs = [Image.fromarray(f) for f in self.frames]
        sample = Image.fromarray(np.vstack(self.frames[:: max(1, len(self.frames) // 12)]))
        pal = sample.quantize(colors=colours, method=Image.Quantize.MEDIANCUT)
        q = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in imgs]
        dur = [max(40, int(round(h * ms))) for h in self.holds]
        dur[-1] = max(dur[-1], tail_ms)
        gif = OUT / f"{name}.gif"
        q[0].save(gif, save_all=True, append_images=q[1:], duration=dur, loop=0, optimize=True, disposal=2)
        wr = imageio.get_writer(OUT / f"{name}.mp4", fps=25, codec="libx264", quality=7, pixelformat="yuv420p",
                                macro_block_size=2, ffmpeg_log_level="error")
        for f, ms_ in zip(self.frames, dur):
            for _ in range(max(1, round(ms_ / 40))):
                wr.append_data(f)
        wr.close()
        Image.fromarray(self.frames[self.key if self.key is not None else -1]).save(OUT / f"{name}_key.png")
        self.pl.close()
        print(f"wrote anim/{name}.gif  {len(q)} frames  {gif.stat().st_size / 1e6:.2f} MB", flush=True)


def ease(i, n):
    return 0.5 - 0.5 * math.cos(math.pi * i / max(1, n - 1))


# ---------------------------------------------------------------------------------------------------------------
# Workholding and tools (lathe axis = x, chuck face at x = 0, work toward +x, operator on -y)
# ---------------------------------------------------------------------------------------------------------------
def chuck_body(r=62.0):
    return cyl_x(r, -42, 0).fuse(cyl_x(r * 0.55, -70, -42))


def chuck_jaws(grip_r, n=3, length=14.0, soft=False):
    """Stepped jaws gripping a diameter 2*grip_r over x in [0, length]."""
    jaws = None
    for k in range(n):
        j = box(-6, length, -7, 7, grip_r, grip_r + 14)
        if not soft:
            j = j.fuse(box(-6, length * 0.45, -7, 7, grip_r + 14, grip_r + 26))
        else:
            j = j.fuse(box(-6, length, -7, 7, grip_r + 14, grip_r + 22))
        j = j.rotate((0, 0, 0), (1, 0, 0), 360.0 / n * k + (45 if n == 4 else 90))
        jaws = j if jaws is None else jaws.fuse(j)
    return jaws


def collet_chuck(r_work):
    body = cyl_x(30, -60, -10)
    nut = cyl_x(22, -10, 8).cut(cyl_x(r_work + 0.3, -11, 9))
    cone = solid(cq.Workplane("YZ").workplane(offset=8).circle(16).workplane(offset=6).circle(r_work + 1.5).loft())
    return body.fuse(nut).fuse(cone).cut(cyl_x(r_work + 0.3, -61, 15))


def turning_tool():
    """80 deg rhombic insert + holder; nose at the origin, cutting toward +y/-x; holder runs to +x, -y."""
    ins = cq.Workplane("XY").polyline([(0.0, 0.0), (8.2, -0.7), (8.9, -8.9), (0.7, -8.2)]).close().extrude(3.6)
    ins = solid(ins).translate(cq.Vector(0, 0, -1.8))
    hold = cq.Workplane("XY").polyline([(6.4, -1.6), (30.0, -15.6), (24.6, -24.7), (1.0, -10.7)]).close().extrude(6.8)
    hold = solid(hold).translate(cq.Vector(0, 0, -3.4))
    shank = box(18, 34, -60, -14, -6, 6)
    return solid(ins), hold.fuse(shank)


def boring_bar(r_bar, reach):
    """Bar along +x; its insert's tip at the origin, cutting the bore wall at +y."""
    tip = box(-1.0, 4.0, -2.5, 0.0, -1.5, 1.5)
    bar = cyl_x(r_bar, 2.0, reach + 40, y=-r_bar - 0.6)
    holder = box(reach + 40, reach + 70, -r_bar - 22, -r_bar + 6, -12, 12)
    return tip, bar.fuse(holder)


def twist_drill(d, length, flute):
    r = d / 2 * 0.97
    tip_h = r / math.tan(math.radians(59))
    prof = [(0, 0), (tip_h, r), (flute, r), (flute, max(r, 3.0)), (length, max(r, 3.0)), (length, 0)]
    return turned(prof)


def parting_blade(w=2.2):
    return box(-w / 2, w / 2, -36, 0, -9, 9)


def dial_indicator():
    """Dial test indicator: probe tip at the origin, stem up, dial facing the operator (-y)."""
    probe = cyl_z(0.9, 0, 6)
    stem = cyl_z(2.0, 6, 16)
    dial = cyl_z(11, 0, 6).rotate((0, 0, 0), (1, 0, 0), 90).translate(cq.Vector(0, 0, 27))
    return probe.fuse(stem).fuse(dial)


def die_holder(r_in=5.0):
    ring = cyl_x(19, 0, 10).cut(cyl_x(r_in, -1, 11))
    handle = cyl_z(4, -95, 95).translate(cq.Vector(5, 0, 0))
    return ring.fuse(handle.cut(cyl_x(19.5, -1, 11)))


def drill_press(head_z=250.0, table_top=0.0, table_r=170.0):
    table = cyl_z(table_r, table_top - 30, table_top)
    col = cyl_z(40, table_top - 400, table_top + 650).translate(cq.Vector(0, 230, 0))
    arm = box(-35, 35, 0, 230, table_top - 60, table_top - 30)
    head = box(-90, 90, 60, 300, head_z + 120, head_z + 330)
    quill = cyl_z(28, head_z + 60, head_z + 125).translate(cq.Vector(0, 0, 0))
    return table.fuse(col).fuse(arm), head, quill


def jacobs_chuck():
    return solid(cq.Workplane("XY").circle(14).workplane(offset=40).circle(22).loft()).fuse(cyl_z(22, 40, 60))


# ---------------------------------------------------------------------------------------------------------------
# Sheet cutting (waterjet / laser) on a slatted table
# ---------------------------------------------------------------------------------------------------------------
def nozzle(waterjet=True):
    if not waterjet:                        # fiber-laser head, drawn for small parts
        tip = solid(cq.Workplane("XY").circle(0.8).workplane(offset=6).circle(4).loft())
        return tip.fuse(cyl_z(7, 6, 40)).fuse(cyl_z(4, 40, 80))
    tip = solid(cq.Workplane("XY").circle(1.2).workplane(offset=14).circle(7 if waterjet else 9).loft())
    body = cyl_z(16 if waterjet else 20, 14, 70).fuse(cyl_z(9, 70, 150))
    if waterjet:
        body = body.fuse(cyl_z(3.0, -0.5, 14))
    return tip.fuse(body)


def slat_table(x0, x1, y0, y1, pitch=45.0):
    slats = None
    x = x0 + 10
    while x < x1 - 5:
        s = box(x - 1.5, x + 1.5, y0 - 20, y1 + 20, -40, -0.2)
        slats = s if slats is None else slats.fuse(s)
        x += pitch
    rim = box(x0 - 40, x1 + 40, y0 - 60, y1 + 60, -70, -40).cut(box(x0 - 25, x1 + 25, y0 - 45, y1 + 45, -71, -39))
    return slats, rim.fuse(box(x0 - 40, x1 + 40, y0 - 60, y1 + 60, -90, -70))


class SheetJob:
    """Flat parts placed on a stock sheet; holes come out one by one, then the outlines, then the parts lift out."""

    def __init__(self, parts, offsets, sheet, t):
        self.t = t
        self.sheet = box(*sheet, 0, t)
        self.parts = [solid(p).translate(cq.Vector(ox, oy, 0)) for p, (ox, oy) in zip(parts, offsets)]
        self.blanks = [blank_of(p) for p in self.parts]
        self.holes = []
        for i, (b, p) in enumerate(zip(self.blanks, self.parts)):
            for h in b.cut(p).Solids():
                c = h.Center()
                self.holes.append((i, h, (c.x, c.y)))
        order = tour([h[2] for h in self.holes], start=(sheet[0], sheet[2]))
        self.holes = [self.holes[k] for k in order]
        self.outlines = []
        for b in self.blanks:
            top = [f for f in b.Faces() if f.geomType() == "PLANE" and abs(f.Center().z - t) < 1e-4][0]
            self.outlines.append(wire_points(top.outerWire(), 160) + np.array([0, 0, 0.25]))

    def hole_path(self, h, n=40):
        top = [f for f in h.Faces() if f.geomType() == "PLANE" and abs(f.Center().z - self.t) < 1e-4]
        return wire_points(top[0].outerWire(), n) + np.array([0, 0, 0.25]) if top else None


def sheet_cut_frames(sc, job: SheetJob, steps, cam, waterjet=True, holes_per_frame=3, outline_frames=5,
                     sheet_color=ALU, table=None, extra=lambda sc: None):
    """steps = (load, holes, outline, lift) step numbers/titles/captions as dicts."""
    noz = cached(("noz", waterjet), lambda: nozzle(waterjet))
    tbl = (mesh(table[0], tol=0.5), mesh(table[1], tol=0.5)) if table is not None else None
    state = job.sheet
    park = (job.sheet.BoundingBox().xmin - 40, job.sheet.BoundingBox().ymax + 30)

    def frame(st, head_xy, kerf=(), parts_out=None, lift=0.0, hold=1.0, key=False, labels=()):
        sc.clear()
        if tbl is not None:
            sc.add(tbl[0], SLAT, lw=0.4, edges=False)
            sc.add(tbl[1], TABLE, lw=0.5)
        sc.add(mesh(state if parts_out is None else parts_out[0], tol=0.1), sheet_color, lw=0.8)
        if parts_out is not None:
            for p in parts_out[1]:
                sc.add(mesh(p, tol=0.1).move((0, 0, lift)), sheet_color, lw=0.9)
        for k in kerf:
            if k is not None and len(k) > 1:
                sc.lines(pv.lines_from_points(k), KERF, 2.2)
        if head_xy is not None:
            sc.add(noz.move((head_xy[0], head_xy[1], job.t + 1.5)), DARKSTEEL, lw=0.6)
        extra(sc)
        sc.camera(*cam)
        sc.grab(st["step"], st["title"], st["caption"], hold=hold, key=key, labels=labels)

    s = steps["load"]
    for i in range(2):
        frame(s, park, hold=6 if i else 3)
    s = steps["holes"]
    done_paths = []
    hs = job.holes
    for g in range(0, len(hs), holes_per_frame):
        grp = hs[g:g + holes_per_frame]
        for _, h, _ in grp:
            state = state.cut(h)
            done_paths.append(job.hole_path(h))
        frame(s, grp[-1][2], kerf=done_paths[-holes_per_frame:], hold=1.4 if g else 3)
    s = steps["outline"]
    for i, pts in enumerate(job.outlines):
        n = len(pts)
        for f in range(outline_frames):
            k = int(n * (f + 1) / outline_frames)
            frame(s, pts[min(k, n - 1)][:2], kerf=[pts[:k]], hold=1.2 if f < outline_frames - 1 else 2,
                  key=(i == 0 and f == outline_frames // 2))
    skeleton = state
    for b in job.blanks:
        skeleton = skeleton.cut(b)
    s = steps["lift"]
    for i in range(4):
        frame(s, park, parts_out=(skeleton, job.parts), lift=ease(i, 4) * 40, hold=1.2 if i < 3 else 6)
    return skeleton


# ---------------------------------------------------------------------------------------------------------------
# 1. Paternoster plates
# ---------------------------------------------------------------------------------------------------------------
def pat_plates():
    D = design("paternoster")
    P = D.P
    front, back, motor = (flat(D.L.shape(k)) for k in ("side_plate_front", "side_plate_back", "motor_plate"))
    fx, fy = front.BoundingBox().xlen, front.BoundingBox().ylen
    mx = motor.BoundingBox().xlen
    gap = 14.0
    sheet = (0.0, 914.4, 0.0, 355.6)  # 14 x 36 in
    x0 = 12.0
    offs = [(x0 + fx / 2, sheet[3] / 2), (x0 + fx + gap + fx / 2, sheet[3] / 2),
            (x0 + 2 * fx + 2 * gap + mx / 2, sheet[3] / 2)]
    job = SheetJob([front, back, motor], offs, sheet, P.PLATE_T_SIDE)
    sc = Scene("Paternoster: side plates (2) + motor plate, 1/4 in 6061", 5)
    cam = ((457, 120, 0), (0.12, -0.62, 0.78), 345)
    tbl = slat_table(*sheet)
    n_front = len(D.L.side_holes(False))
    steps = {
        "load": dict(step=1, title="Load the sheet",
                     caption="1/4 in (6.35 mm) 6061-T6. Front and back side plates (320 x 345 mm) and the 120 mm motor plate "
                             "nest on a 14 x 36 in piece. A 12 x 24 in plate can't hold even one side plate: both sides are over "
                             "12 in. SendCutSend: upload dxf/side_plate_front, side_plate_back, motor_plate."),
        "holes": dict(step=2, title="Pierce and cut the holes first",
                      caption=f"Waterjet (or fiber laser). Holes before outlines so nothing shifts: {n_front} in the front plate, "
                              f"{len(D.L.side_holes(True))} in the back, 9 in the motor plate. All are clearance holes "
                              "(49 mm for the flange units' dome, 6.9 mm for 1/4-20, 10.5 mm slots for the M10 axles, 5.5 mm "
                              "for M5, 6.6 mm for the standoffs): +-0.2 mm is plenty, nothing to tap."),
        "outline": dict(step=3, title="Cut the outlines",
                        caption="R8 corners on the side plates, R6 on the motor plate. If the shop leaves micro-tabs, snap the "
                                "parts out and file the nubs flush."),
        "lift": dict(step=4, title="Lift the parts out",
                     caption="The skeleton stays on the slats. About 20 min of waterjet time for all three; SendCutSend "
                             "ships in 3-5 days."),
    }
    sheet_cut_frames(sc, job, steps, cam, waterjet=True, holes_per_frame=3, outline_frames=4, table=tbl)
    # 5: deburr and check, front plate alone with callouts (anchors from the CAD's own hole solids)
    holes = blank_of(front).cut(front).Solids()
    big = max(holes, key=lambda h: h.Volume())
    slot = max(holes, key=lambda h: abs(h.BoundingBox().xlen - h.BoundingBox().ylen))
    cb, cs = big.Center(), slot.Center()
    rb = big.BoundingBox().xlen / 2
    t = P.PLATE_T_SIDE
    for i in range(3):
        sc.clear()
        sc.add(mesh(front, tol=0.1), ALU, lw=0.9)
        sc.camera((0, -45, 0), (0.1, -0.55, 0.83), 230)
        labels = [("49 mm: clears the flange\nunit's 47 mm rear dome", (cb.x, cb.y + rb, t), (0.06, 0.24)),
                  ("10.5 x 24.5 mm slot: the M10\nidler axle slides 14 mm", (cs.x, cs.y, t), (0.70, 0.24))]
        sc.grab(5, "Deburr and check",
                "Deburr every edge and hole on both faces (hand deburring tool, then a file). Check: a 1/4-20 bolt drops through "
                "both bolt holes of a flange unit laid on the plate; an M10 bolt slides the full slot; bearing holes 190.5 mm "
                "apart (+-0.3). Back plate: 4 x 6.6 mm standoff holes on 56 x 104 mm. Motor plate: NEMA 34 pilot 73.6 mm.",
                hold=8 if i == 2 else 2, labels=labels if i == 2 else ())
    sc.save("pat_plates")


# ---------------------------------------------------------------------------------------------------------------
# 5. Chain carousel v2 plates: cut, then tap the eight M5 holes
# ---------------------------------------------------------------------------------------------------------------
def flat_with_points(shape, pts):
    """flat() for a shape already in its plate frame (thin axis z), also mapping 2-D points in that frame."""
    s = solid(shape)
    bb = s.BoundingBox()
    rot = bb.ylen > bb.xlen
    out = []
    for (x, y) in pts:
        x_, y_ = x - bb.center.x, y - bb.center.y
        out.append((-y_, x_) if rot else (x_, y_))
    return flat(s), out


def v2_plates():
    D = design("chain-carousel-v2")
    P = D.P
    taps = {b: [h[1] for h in D.L.side_holes(b) if h[0] == "tap"] for b in (False, True)}
    front, tf = flat_with_points(D.L.shape("side_plate_front"), taps[False])
    back, tb = flat_with_points(D.L.shape("side_plate_back"), taps[True])
    fx, bx = front.BoundingBox().xlen, back.BoundingBox().xlen
    sheet = (0.0, 914.4, 0.0, 304.8)  # 12 x 36 in
    g = (sheet[1] - fx - bx) / 3
    offs = [(g + fx / 2, sheet[3] / 2), (2 * g + fx + bx / 2, sheet[3] / 2)]
    job = SheetJob([front, back], offs, sheet, P.PLATE_T_SIDE)
    sc = Scene("Chain carousel v2: side plates, 1/4 in 6061", 5)
    cam = ((457, 110, 0), (0.12, -0.62, 0.78), 330)
    tbl = slat_table(*sheet)
    steps = {
        "load": dict(step=1, title="Load one 12 x 36 in plate",
                     caption=f"1/4 in 6061-T651 (FixSupply SHT-6061-0.25X12-36). Front {fx:.0f} x {front.BoundingBox().ylen:.0f} "
                             f"and back {bx:.0f} x {back.BoundingBox().ylen:.0f} mm fit end to end with {g:.0f} mm between. "
                             "Or upload dxf/side_plate_front and side_plate_back to SendCutSend."),
        "holes": dict(step=2, title="Cut the holes first",
                      caption=f"Waterjet. {len(job.holes)} openings: bearing domes and slotted bolt holes (top corners slotted "
                              "+8/-6 mm for chain tension), M5 clearance 5.5 mm, the motor's slotted pilot on the back plate, "
                              "and eight 4.2 mm tap-drill holes for the tensioner blocks (if the jet tapers them, cut 2 mm "
                              "pilots and drill 4.2 on the drill press)."),
        "outline": dict(step=3, title="Cut the outlines",
                        caption="R6 corners. Snap off any micro-tabs and file flush."),
        "lift": dict(step=4, title="Lift them out and deburr",
                     caption="Deburr both faces of every edge and hole. Check: the bearing slots let a 1/4-20 bolt slide the "
                             "full 14 mm; plates are flat within 0.5 mm on the bench."),
    }
    sheet_cut_frames(sc, job, steps, cam, waterjet=True, holes_per_frame=4, outline_frames=4, table=tbl)
    # step 5: tap the M5 holes on the drill press (front plate shown; back plate the same)
    table, head, _ = drill_press(head_z=70.0, table_top=0.0, table_r=150)
    m_table, m_head = mesh(table, tol=0.3), mesh(head, tol=0.3)
    chuck = cached("jacobs", jacobs_chuck)
    tap = cached("tap_m5", lambda: twist_drill(5.0, 70, 22))
    plate = mesh(front, tol=0.1)
    t = P.PLATE_T_SIDE
    done = []
    order = sorted(range(len(tf)), key=lambda i: tf[i][0])
    cap = ("Drill press as a tap guide: spindle OFF, M5 x 0.8 spiral-point tap in the chuck, turn it by hand with the "
           "quill lightly down, tapping fluid; or a tapping head at 200 rpm. Through 6.35 mm = 1.3 D of thread. "
           "Check: an M5 x 10 SHCS runs in by hand. Repeat on the back plate's four (8 in all).")
    for n, i in enumerate(order):
        hx, hy = tf[i]
        for f, dz in enumerate((40.0, 6.0, -8.0)):
            sc.clear()
            sc.add(m_table, TABLE, lw=0.4)
            sc.add(plate.move((-hx, -hy, 0)), ALU, lw=0.8)
            for (ox, oy) in done:
                sc.lines(helix_lines(0, t, 2.55, 0.8).rotate_y(-90, inplace=False).translate((ox - hx, oy - hy, 0)
                                                                                           , inplace=False), "#30343a", 1.5)
            z = t + dz
            sc.add(tap.rot("y", -90).move((0, 0, z)), DARKSTEEL, lw=0.5)
            sc.add(chuck.move((0, 0, z + 70)), CHUCK, lw=0.5)
            sc.add(mesh(cyl_z(20, z + 128, 200)), JAW, lw=0.4)
            sc.add(m_head, "#4f6b5a", lw=0.4)
            sc.camera((0, 30, 30), (0.45, -0.75, 0.55), 115)
            sc.grab(5, f"Tap the M5 holes ({n + 1} of 4 on this plate)", cap, hold=1.2 if f < 2 else 1.6,
                    key=(n == 1 and f == 1))
        done.append((hx, hy))
    sc.save("v2_plates")


# ---------------------------------------------------------------------------------------------------------------
# Lathe frames
# ---------------------------------------------------------------------------------------------------------------
LATHE_DIR = (0.38, -0.92, 0.55)


def lathe_frame(sc, hold_meshes, work: Mesh, spin, tools=(), cam=None, work_spins=True, lines=(), **kw):
    sc.clear()
    for m, col in hold_meshes:
        sc.add(m.rot("x", spin), col, lw=0.6)
    sc.add(work.rot("x", spin if work_spins else 0.0), STEEL if kw.pop("steel", True) else ALU, lw=1.0)
    for m, col in tools:
        sc.add(m, col, lw=0.7)
    for ln in lines:
        if ln is not None:
            sc.lines(ln.rotate_x(spin if work_spins else 0.0, inplace=False), "#30343a", 1.3)
    sc.camera(*cam)
    sc.grab(**kw)


def lathe_pose(s, z_end_at_x):
    """Part axis z -> lathe axis x (rotate about y by +90: z -> x, x -> -z); the part's lowest z lands at x = z_end_at_x."""
    s = solid(s).rotate((0, 0, 0), (0, 1, 0), 90)
    bb = s.BoundingBox()
    return s.translate(cq.Vector(z_end_at_x - bb.xmin, 0, 0))


def bore_passes(sc, shape0, radii, x_in, x_out, hold_meshes, cam, step, title, caption, note, spin0, bar_r, tip_col=CARBIDE,
                frames=3, key_at=None, sec_col=SECTION):
    """Boring passes from x_out (outer face) to x_in (through); returns the final shape and spin."""
    tip, bar = (mesh(m) for m in boring_bar(bar_r, 80))
    s = shape0
    spin = spin0
    for pi, r in enumerate(radii):
        for f in range(frames):
            xt = x_out + 2 - (x_out + 2 - x_in) * (f + 1) / frames
            cur = s.cut(cyl_x(r, xt, x_out + 30))
            if f == frames - 1:
                cur = s.cut(cyl_x(r, x_in - 5, x_out + 30))
            show = mesh(halve(cur), section_y=0.0)
            tools = [(tip.move((xt, r, 0)), tip_col), (bar.move((xt, r, 0)), TOOL)]
            lathe_frame(sc, hold_meshes, show, spin, tools=tools, cam=cam, work_spins=False, step=step, title=title,
                        caption=caption.format(d=2 * r), note=note, hold=1.0 if f < frames - 1 else 1.6,
                        key=(key_at == (pi, f)))
            spin += 27
        s = s.cut(cyl_x(r, x_in - 5, x_out + 30))
    return s, spin


# ---------------------------------------------------------------------------------------------------------------
# Arbor press frames (press axis = z, base plate top at z = 0, column behind at +y)
# ---------------------------------------------------------------------------------------------------------------
def press_frame(sc, ram_z, items, cam, ram_w=30.0, **kw):
    sc.clear()
    frame = cached("press_frame", lambda: box(-120, 120, -90, 90, -45, 0).fuse(box(-55, 55, 90, 150, -45, 330))
                   .fuse(box(-65, 65, -30, 150, 250, 330)).cut(cyl_z(20, -50, 1)), tol=0.4)
    sc.add(frame, "#4f6b5a", lw=0.5)
    sc.add(mesh(box(-ram_w / 2, ram_w / 2, -ram_w / 2, ram_w / 2, ram_z, 420)), DARKSTEEL, lw=0.6)
    for m, col in items:
        sc.add(m, col, lw=0.8)
    sc.camera(*cam)
    sc.grab(**kw)


# ---------------------------------------------------------------------------------------------------------------
# 2. Paternoster: re-bore four 35BS32 to 35 mm H7, press in two 6202-2RS
# ---------------------------------------------------------------------------------------------------------------
def pat_sprocket():
    D = design("paternoster")
    P = D.P
    bought = solid(D.PT.sprocket_32())
    final = solid(D.L.shape("sprocket_32_idler"))
    brg = solid(D.L.shape("bearing_6202"))
    sc = Scene("Paternoster: top idler sprocket, 35BS32 re-bored (x4)", 5)
    w0 = lathe_pose(bought, 2.0)
    x_out = 2.0 + P.LTB
    jaws = cached("jaws4_hub32", lambda: chuck_jaws(P.HUB_D / 2, n=4, length=12))
    body = cached("chuck_big", lambda: chuck_body(70))
    hold = [(body, CHUCK), (jaws, JAW)]
    cam = ((24, 0, 6), LATHE_DIR, 68)
    ind = cached("indicator", dial_indicator)
    xr = x_out - P.TOOTH_W / 2
    spin = 0.0
    m0 = mesh(w0, tol=0.08)
    cap1 = ("4-jaw chuck on the 2 in hub, hub face on parallels so the bar can come out the back. Lay a 0.200 in pin "
            "in a tooth gap and indicate it at 4 places; move jaws until under 0.05 mm, so the new bore is true to the "
            "pitch circle, not to the old bore.")
    for i in range(6):
        lathe_frame(sc, hold, m0, spin, tools=[(ind.move((xr, 0, P.OD / 2)), "#d9dde2")], cam=cam, step=1,
                    title="Chuck the hub, dial in on the teeth", caption=cap1, hold=1.0 if i < 5 else 3)
        spin += 15
    cap2 = ("Carbide boring bar (10 mm shank), 450 rpm, 0.1 mm/rev, 1-1.5 mm a side per pass, cutting oil. "
            "Now {d:.1f} mm: the 5/8 in bore and its keyway are gone after the first pass.")
    s, spin = bore_passes(sc, w0, [10.5, 13.0, 15.5, 17.25], 2.0, x_out, hold, cam, 2, "Bore it out",
                          cap2, "cut in half so you can see in", spin, 4.6, key_at=(2, 1))
    cap3 = ("Leave 0.2 mm, take two 0.1 mm passes and a spring pass at 0.05 mm/rev: 35.000-35.025 mm (H7) the whole "
            "22.2 mm. Check with a bore gauge set on a 35 mm ring or micrometer. Chamfer both edges 0.5 mm; deburr the "
            "set-screw hole where it breaks into the bore.")
    s, spin = bore_passes(sc, s, [P.IDLER_BORE / 2], 2.0, x_out, hold, cam, 3, "Finish to 35 H7", "{d:.2f} mm. " + cap3,
                          "cut in half so you can see in", spin, 4.6, frames=4)
    # sanity: the lathe result is the CAD's idler sprocket
    ref = lathe_pose(final, 2.0)
    dv = abs(s.Volume() - ref.Volume())
    print(f"pat_sprocket: lathe result vs CAD idler volume diff {dv:.1f} mm3 (of {ref.Volume():.0f})", flush=True)
    # 4: press two bearings in, sprocket hub-down on the press plate; the pair's position comes from the layout
    hub0 = P.LTB - P.TOOTH_W / 2                                   # hub face -> tooth-ring centre plane
    zc = [x + hub0 for x in getattr(P, "IDLER_BRG_X", (5.5 - hub0, 16.5 - hub0))]   # bearing centres above the hub face
    prot = max(0.0, 5.5 - zc[0])                                   # the pair stands this far out of the hub face
    spr = mesh(halve(final.translate(cq.Vector(0, 0, hub0 + prot))), section_y=0.0)
    shim = (mesh(halve(cyl_z(P.HUB_D / 2, 0, prot).cut(cyl_z(18.5, -1, prot + 1))), section_y=0.0)
            if prot > 0.05 else None)
    bm = mesh(halve(brg), section_y=0.0)
    drv = mesh(halve(cyl_z(17.0, 0, 10).fuse(cyl_z(12, 10, 30))), section_y=0.0)
    cam_p = ((0, 0, 40), (0.35, -0.9, 0.42), 105)
    cap4 = (f"Arbor press, sprocket hub-down on a {prot:.1f} mm ring shim (ID over 35 mm) on a flat plate. Loctite 641 "
            "on the outer rings; push on the outer ring only (a 34 mm driver). The first bearing stops on the plate, "
            f"{prot:.1f} mm out of the hub face as drawn; the second stops on the first." if prot > 0.05 else
            "Arbor press, sprocket hub-down on a flat plate. Loctite 641 on the outer rings; push on the outer ring only "
            "(a 34 mm driver). The first bearing stops on the plate, flush with the hub face; the second on the first.")
    placed = []
    for b, zf in enumerate((5.5, 16.5)):
        for i in range(6):
            z = 70 - (70 - zf) * ease(i, 6)
            items = [(spr, STEEL)] + ([(shim, BRASS)] if shim is not None else [])
            items += [(bm.move((0, 0, zz)), BEARING) for zz in placed] + [(bm.move((0, 0, z)), BEARING),
                                                                         (drv.move((0, 0, z + 5.5)), DARKSTEEL)]
            press_frame(sc, z + 35.5, items, cam_p, step=4, title=f"Press in two 6202-2RS ({b + 1} of 2)", caption=cap4,
                        note="cut in half so you can see in", hold=1.0 if i < 5 else 2)
        placed.append(zf)
    # 5: finished part
    fin = mesh(final.translate(cq.Vector(0, 0, hub0)), tol=0.08)
    bw = mesh(brg)
    for i in range(8):
        sc.clear()
        sc.add(fin.rot("z", 6 * i), STEEL, lw=0.9)
        for zz in zc:
            sc.add(bw.move((0, 0, zz)), BEARING, lw=0.7)
        sc.camera((0, 0, 11), (0.3, -0.75, 0.6), 62)
        sc.grab(5, "The idler sprocket", "32T #35, 35 H7 bore, two 6202-2RS (15 x 35 x 11) side by side, standing "
                f"{prot:.1f} mm out of the hub so the axle's circlip stays inside the tooth face. Rides on the fixed 15 mm "
                "idler axle (process 3). Make four. About 1 h each on a manual lathe.", hold=1.0 if i < 7 else 8)
    sc.save("pat_sprocket")


# ---------------------------------------------------------------------------------------------------------------
# 6. Chain carousel v2: re-bore the motor's 15T sprocket to 14 H7, broach a 5 mm keyway
# ---------------------------------------------------------------------------------------------------------------
def v2_sprocket():
    D = design("chain-carousel-v2")
    P = D.P
    bought = solid(D.PT.sprocket(P.N15, 12.7, P.HUB15_D, P.LTB15, (3.175, 1.5875)))   # 35BS15H-1/2 as sold: 1/8 in key
    final = solid(D.L.shape("sprocket_15_motor"))
    sc = Scene("Chain carousel v2: motor sprocket, 35BS15H-1/2 -> 14 mm + 5 mm key", 5)
    w0 = lathe_pose(bought, 2.0)
    x_out = 2.0 + P.LTB15
    jaws = cached("jaws3_hub15", lambda: chuck_jaws(P.HUB15_D / 2, n=3, length=11))
    body = cached("chuck_mid", lambda: chuck_body(55))
    hold = [(body, CHUCK), (jaws, JAW)]
    cam = ((14, 0, 2), LATHE_DIR, 46)
    ind = cached("indicator", dial_indicator)
    od15 = P.P * (0.6 + 1 / math.tan(math.pi / P.N15))
    spin = 0.0
    m0 = mesh(w0, tol=0.06)
    for i in range(5):
        lathe_frame(sc, hold, m0, spin, tools=[(ind.move((x_out - P.TOOTH_W / 2, 0, od15 / 2)), "#d9dde2")],
                    cam=cam, step=1, title="Chuck the hub, check the teeth",
                    caption="3-jaw chuck on the 34.1 mm hub, hub face 2 mm proud of the jaws so the bar can run out. "
                            "Indicate the tooth tips: under 0.1 mm runout, or shim a jaw (or use the 4-jaw).",
                    hold=1.0 if i < 4 else 3)
        spin += 20
    cap = ("Small boring bar (8 mm shank), 700 rpm, 0.05-0.08 mm/rev; 0.4, 0.2, then 0.05 mm a side. Now {d:.2f} mm. "
           "14.000-14.018 mm (H7): the NEMA 34's 14 mm shaft slides in with no shake. Chamfer the edges 0.5 mm.")
    s, spin = bore_passes(sc, w0, [6.75, 6.95, P.M34_SHAFT_D / 2], 2.0, x_out, hold, cam, 2, "Bore 1/2 in out to 14 H7",
                          cap, "cut in half so you can see in", spin, 3.6, key_at=(1, 1))
    # 3: broach on the arbor press: part hub-down, keyway at +y
    up = lambda sh: solid(sh).translate(cq.Vector(0, 0, P.LTB15 - P.TOOTH_W / 2))
    bored = up(bought.cut(cyl_z(P.M34_SHAFT_D / 2, -40, 40)))
    kw, kd = 5.0, 2.3
    r = P.M34_SHAFT_D / 2
    bush = cyl_z(r - 0.02, -40, P.LTB15 + 12).cut(box(-kw / 2 - 0.1, kw / 2 + 0.1, r - 4.0, r + 1, -41, P.LTB15 + 13))
    bush = bush.fuse(cyl_z(r + 5, P.LTB15 + 12, P.LTB15 + 16).cut(box(-kw / 2 - 0.1, kw / 2 + 0.1, r - 4.0, r + 6, 0, 100)))
    m_bush = mesh(halve(bush), section_y=0.0)
    cam_p = ((0, 0, 20), (0.35, -0.9, 0.42), 70)
    capb = ("Arbor press, sprocket hub-down. 5 mm push broach in a 14 mm slotted bushing, lined up with the old 1/8 in "
            "keyway so it disappears. Oil it; one stroke, add the shim, a second stroke. Width 5.00-5.03 mm, 16.3 mm "
            "from the far bore wall to the keyway floor (14 + 2.3).")
    for ps, depth in enumerate((1.6, kd)):
        for i in range(6):
            zt = P.LTB15 + 30 - (P.LTB15 + 30 + 25) * ease(i, 6)  # broach tip height
            cut_to = max(zt, -1)
            cur = bored
            if ps == 1:
                cur = cur.cut(box(-kw / 2, kw / 2, r - 1, r + 1.6, -5, P.LTB15 + 5))
            if cut_to < P.LTB15:
                cur = cur.cut(box(-kw / 2, kw / 2, r - 1, r + depth, cut_to, P.LTB15 + 5))
            broach = box(-kw / 2 + 0.05, kw / 2 - 0.05, r - 4.0 + (0.7 if ps else 0), r + depth - 0.05, zt, zt + 230)
            items = [(mesh(halve(cur), section_y=0.0), STEEL), (m_bush, BRASS), (mesh(halve(broach), section_y=0.0), DARKSTEEL)]
            press_frame(sc, zt + 230, items, cam_p, ram_w=26, step=3, title=f"Broach the 5 mm keyway (stroke {ps + 1} of 2)",
                        caption=capb, note="cut in half so you can see in", hold=1.0 if i < 5 else 2, key=(ps == 0 and i == 3))
    finm = mesh(final, tol=0.06)
    print(f"v2_sprocket: lathe+broach vs CAD volume diff {abs(cur.Volume() - up(final).Volume()):.1f} mm3", flush=True)
    for i in range(6):
        sc.clear()
        sc.add(finm.rot("z", 10 * i), STEEL, lw=0.9)
        sc.camera((0, 0, -6), (0.15, -0.55, 0.82), 34)
        sc.grab(4, "Check it on the motor", "Check: the motor's 5 mm key slides in the keyway and the sprocket slides onto "
                "the 14 mm shaft with the key in, no rock. Set screws (Loctite 243) on the key and at 90 deg. About 45 min.",
                hold=1 if i < 5 else 8)
    sc.save("v2_sprocket")


# ---------------------------------------------------------------------------------------------------------------
# 9. Both designs: face the steel pinion's hub off (KHK SS1-20A)
# ---------------------------------------------------------------------------------------------------------------
HUB_KHK = 8.0   # SS1-20A hub: 16 mm x 10 mm, M4 set screw 5 mm from the hub end (cad/vendor/files/khk/gear_SS1-20A.txt)


def pinion():
    D = design("chain-carousel-v2")
    fin = solid(D.L.shape("pinion"))
    bought = fin.fuse(cyl_z(HUB_KHK, 10.0, 20.0)).cut(cyl_z(2.5, -1, 21))
    bought = bought.cut(cq.Solid.makeCylinder(1.65, 10, cq.Vector(0, 0, 15.0), cq.Vector(0, 1, 0)))  # M4 set-screw hole
    sc = Scene("Both designs: steel pinion KHK SS1-20A, hub faced off (x1 per design)", 4)
    w0 = lathe_pose(bought, 0.0)
    jaws = cached("softjaws22", lambda: chuck_jaws(11.0, n=3, length=9, soft=True))
    body = cached("chuck_small", lambda: chuck_body(42))
    hold = [(body, CHUCK), (jaws, SOFTJAW)]
    cam = ((17, 0, 2), LATHE_DIR, 33)
    tip, holder = (mesh(m) for m in turning_tool())
    spin = 0.0
    m0 = mesh(w0, tol=0.03)
    for i in range(4):
        lathe_frame(sc, hold, m0, spin, cam=cam, step=1, title="Soft jaws on the teeth",
                    caption="KHK SS1-20A as sold: 22 mm OD, 10 mm face, 16 x 10 mm hub with an M4 set screw, S45C, not "
                            "hardened (under 194 HB). Take the set screw out. Aluminium soft jaws bored to 22.0 mm (the tip diameter) with a step: "
                            "the gear face sits on the step, the hub sticks out. 1500 rpm.", hold=1 if i < 3 else 3)
        spin += 30
    s = w0
    ends = [17.5, 15.0, 12.5, 10.6, 10.2, 10.0]
    end = 20.0
    for pi, e in enumerate(ends):
        for f in range(3):
            rt = HUB_KHK + 1 - (HUB_KHK + 1 - 2.4) * (f + 1) / 3
            cur = s.cut(cyl_x(HUB_KHK + 2, e, end + 1).cut(cyl_x(rt, e - 1, end + 2)))
            if f == 2:
                cur = s.cut(cyl_x(HUB_KHK + 2, e, end + 1))
            tools = [(tip.move((e, -rt, 0)), CARBIDE), (holder.move((e, -rt, 0)), TOOL)]
            lathe_frame(sc, hold, mesh(cur, tol=0.03), spin, tools=tools, cam=cam, step=2, title="Face the hub off",
                        caption=f"Carbide facing tool, 1500 rpm, 0.05 mm/rev, from the OD in to the bore. 2.5 mm passes, then "
                                f"0.4 and 0.2 mm, and stop on the gear face: hub now {max(e - 10, 0):.1f} mm. S45C turns "
                                "like 1045; don't cut into the teeth.", hold=1 if f < 2 else 1.5, key=(pi == 1 and f == 1))
            spin += 30
        s = s.cut(cyl_x(HUB_KHK + 2, e, end + 1))
        end = e
    ref = lathe_pose(fin, 0.0)
    print(f"pinion: vs CAD volume diff {abs(s.Volume() - ref.Volume()):.2f} mm3", flush=True)
    for i in range(3):
        lathe_frame(sc, hold, mesh(ref, tol=0.03), spin, cam=cam, step=3, title="Chamfer the bore, check the width",
                    caption="Break the bore edge 0.3 mm. Check: 10.00 mm (-0.1/0) across the faces at three places "
                            "(micrometer); the faced side runs true to the bore within 0.02 mm on a 5 mm pin.",
                    hold=1 if i < 2 else 4)
        spin += 30
    fm = mesh(fin, tol=0.03)
    for i in range(6):
        sc.clear()
        sc.add(fm.rot("z", 6 * i), STEEL, lw=0.9)
        sc.camera((0, 0, 5), (0.3, -0.7, 0.65), 15)
        sc.grab(4, "The pinion", "20T module 1, 10 mm wide, 5 mm H7 bore, no hub: it fits in front of the dock magnet. "
                "Bond to the NEMA 11 shaft with Loctite 638 (clean both with acetone). About 30 min.", hold=1 if i < 5 else 8)
    sc.save("pinion")


# ---------------------------------------------------------------------------------------------------------------
# 3. Paternoster: turn four idler axles from 15 mm 1045 rod
# ---------------------------------------------------------------------------------------------------------------
def pat_axle():
    D = design("paternoster")
    P = D.P
    axle = solid(D.L.shape("idler_axle"))
    turned_part = axle.intersect(cyl_z(7.5, -80, 80))          # seat + stem: what comes off the lathe
    washer = axle.cut(cyl_z(7.5, -80, 80))                      # 22 mm x 4 mm ring: the shoulder
    spacer = solid(D.PT.idler_spacer())
    clip = solid(D.PT.idler_circlip())
    brg = solid(D.L.shape("bearing_6202"))
    bb = axle.BoundingBox()
    L_stem, L_seat = -bb.zmin, bb.zmax                          # from the CAD: 21.35 stem, 34.9 seat
    L_tot = L_stem + L_seat
    g_d = P.IDLER_CIRCLIP[0]                                    # circlip groove diameter
    gfaces = [q.BoundingBox() for q in axle.Faces() if q.geomType() == "CYLINDER" and abs(q.BoundingBox().xlen - g_d) < 0.01]
    g_at, g_end = min(q.zmin for q in gfaces), max(q.zmax for q in gfaces)   # groove from the shoulder (32.7 .. 33.8)
    land = L_seat - g_end
    zc = [x - P.SIDE_IN for x in P.IDLER_BRG_X]                 # bearing centres from the shoulder face
    prot = 5.5 - (P.LTB - P.TOOTH_W / 2) - P.IDLER_BRG_X[0]     # the pair stands this far out of the hub face (2.2)
    sp_i, sp_o, sp_l = P.IDLER_SPACER
    sc = Scene("Paternoster: idler axle from 15 mm 1045 rod (x4) + spacer", 8)
    coll = cached("collet15", lambda: collet_chuck(7.5))
    hold = [(coll, CHUCK)]
    xe = 14 + L_tot + 6.0                                       # free end of the bar (the stem end)
    x_sh = xe - L_stem                                          # the shoulder face
    cam = ((52, 0, 0), LATHE_DIR, 46)
    tip, holder = (mesh(m) for m in turning_tool())
    spin = 0.0

    def bar(end, stem_r=7.5, stem_from=None, ch=0.0, groove=None, part=None):
        prof = [(-40, 0), (-40, 7.5)]
        if part is not None:
            p0, pr = part
            prof += [(p0 - 2.2, 7.5), (p0 - 2.2, pr), (p0, pr), (p0, 7.5)]
        if groove is not None:
            g0, g1, gr = groove
            prof += [(g0, 7.5), (g0, gr), (g1, gr), (g1, 7.5)]
        if stem_from is not None and stem_r < 7.5:
            prof += [(stem_from, 7.5), (stem_from, stem_r), (end - ch, stem_r), (end, stem_r - ch)]
        else:
            prof += [(end, 7.5)]
        prof += [(end, 0)]
        return turned(prof)

    for i in range(3):
        lathe_frame(sc, hold, mesh(bar(xe + 0.3)), spin, cam=cam, step=1, title="Chuck the 15 mm rod",
                    caption="1045 rod, 15 mm -0.013/0 (McMaster 5615N15), in a 15 mm ER collet, about 65 mm out. Leave the "
                            "OD alone: the bar's own ground finish is the 6202 seat (h6-h7).", hold=1 if i < 2 else 3)
        spin += 33
    for f in range(3):
        r = 7.5 * (1 - (f + 1) / 3)
        lathe_frame(sc, hold, mesh(bar(xe + 0.3 - 0.3 * (f + 1) / 3)), spin,
                    tools=[(tip.move((xe, -max(r, 0.3), 0)), CARBIDE), (holder.move((xe, -max(r, 0.3), 0)), TOOL)],
                    cam=cam, step=2, title="Face the end", caption="Carbide tool, 1000 rpm, 0.1 mm/rev, take 0.3 mm.")
        spin += 33
    for pi, r in enumerate((6.5, 5.5, 4.95)):
        for f in range(3):
            xt = xe - (xe - x_sh) * (f + 1) / 3
            lathe_frame(sc, hold, mesh(bar(xe, stem_r=r, stem_from=xt)), spin,
                        tools=[(tip.move((xt, -r, 0)), CARBIDE), (holder.move((xt, -r, 0)), TOOL)],
                        cam=cam, step=3, title="Turn the M10 stem",
                        caption=f"Down to 9.85-9.95 mm (just under M10 major) over {L_stem:.2f} mm (plate + 15: 3 mm past the "
                                f"nylock and its washer). 1000 rpm, 0.1 mm/rev, 1 mm a side, then a 0.1 mm finish. Now {2 * r:.1f} mm.",
                        hold=1 if f < 2 else 1.4, key=(pi == 1 and f == 1))
            spin += 33
    dh = cached("die", die_holder)
    b = mesh(bar(xe, 5.0, x_sh, ch=0.8))
    for f in range(6):
        xd = xe + 3 - (xe + 3 - x_sh - 2) * f / 5
        lathe_frame(sc, hold, b, spin, tools=[(dh.move((xd, 0, 0)), DARKSTEEL)], cam=cam,
                    lines=[helix_lines(xd, xe - 0.8, 5.05, 1.5)], step=4, title="Chamfer 0.8 mm, thread M10 x 1.5",
                    caption="Chamfer the end 0.8 x 45 deg so the die starts. Round die in a tailstock die holder, lathe in "
                            "neutral, turn the chuck by hand; cutting oil, back off half a turn every turn. (Or single-point at "
                            "150 rpm.) Check: an M10 nut runs on by hand to the shoulder.", hold=1.2, work_spins=False)
        spin += 10
    th = helix_lines(x_sh + 1.5, xe - 0.8, 5.05, 1.5)
    xg1 = x_sh - g_at                                           # groove's bearing-side wall
    xg0 = x_sh - g_end                                          # groove's outer wall (the land beyond it)
    xp = x_sh - L_seat                                          # seat end = cut-off line
    gblade = cached("gblade11", lambda: box(-0.55, 0.55, -30, 0, -6, 6))
    for f in range(3):
        gr = 7.5 - (7.5 - g_d / 2) * (f + 1) / 3
        lathe_frame(sc, hold, mesh(bar(xe, 5.0, x_sh, ch=0.8, groove=(xg0, xg1, gr))), spin,
                    tools=[(gblade.move(((xg0 + xg1) / 2, -gr, 0)), TOOL)], cam=cam, lines=[th], step=5,
                    title="Groove for the DIN 471-15 circlip",
                    caption=f"1.1 mm grooving insert, 500 rpm, oil: to {g_d:.1f} mm across (-0.1/0), {g_at:.1f}-{g_end:.1f} mm "
                            f"from the shoulder, leaving a {land:.1f} mm full-diameter land beyond it for the ring to bear on. "
                            "Check: the circlip snaps in and sits square.", hold=1.3, work_spins=False)
    blade = cached("blade", parting_blade)
    for f in range(4):
        r = 7.5 - 7.3 * (f + 1) / 4
        lathe_frame(sc, hold, mesh(bar(xe, 5.0, x_sh, ch=0.8, groove=(xg0, xg1, g_d / 2), part=(xp, r))), spin,
                    tools=[(blade.move((xp - 1.1, -r, 0)), TOOL)], cam=cam, lines=[th], step=6,
                    title=f"Part off at {L_tot:.2f} mm",
                    caption=f"2.2 mm parting blade, 400 rpm, steady feed, oil: {L_seat:.1f} mm seat + {L_stem:.2f} mm stem. "
                            "Catch the part; flip it in the collet (wrap the thread), face to length, break the edge 0.5 mm.",
                    hold=1.2, work_spins=False)
    # 7: the spacer, from 3/4 in 6061 tube (0.125 in wall, 12.7 bore) bored to 15.2 and parted at 7.9
    coll2 = cached("collet19", lambda: collet_chuck(19.05 / 2))
    te = 14 + sp_l + 12.0
    ro = 19.05 / 2

    def tube(ri, end, ri_to=None, part=None):
        x_in = end - 30 if ri_to is None else ri_to
        prof = [(-30, 6.35), (-30, ro)]
        if part is not None:
            p0, pr = part
            prof += [(p0 - 2.2, ro), (p0 - 2.2, pr), (p0, pr), (p0, ro)]
        prof += [(end, ro), (end, ri), (x_in, ri), (x_in, 6.35)]
        return turned(prof)

    bbar_tip, bbar = (mesh(m) for m in boring_bar(3.0, 40))
    cam2 = ((te - 12, 0, 0), LATHE_DIR, 30)
    for f in range(4):
        xt = te + 2 - (sp_l + 4) * (f + 1) / 4
        cur = tube(sp_i / 2, te, ri_to=max(xt, te - sp_l - 3))
        lathe_frame(sc, [(coll2, CHUCK)], mesh(halve(cur), section_y=0.0), 0.0,
                    tools=[(bbar_tip.move((xt, sp_i / 2, 0)), CARBIDE), (bbar.move((xt, sp_i / 2, 0)), TOOL)],
                    cam=cam2, step=7, title=f"Spacer: bore 3/4 in tube to {sp_i:.1f} mm",
                    note="cut in half so you can see in",
                    caption=f"3/4 in 6061 tube, 1/8 in wall (1/2 in bore), in a 3/4 in collet. Small boring bar, 1200 rpm, "
                            f"0.08 mm/rev, to {sp_i:.2f} mm (+0.05/0): it slides on the 15 mm seat. The OD stays as bought "
                            f"(19.05; the CAD says {sp_o:.0f}): it bears on the 6202's inner ring only.", hold=1.2,
                    work_spins=False, steel=False)
    for f in range(3):
        r = ro - (ro - sp_i / 2 + 0.3) * (f + 1) / 3
        cur = tube(sp_i / 2, te, ri_to=te - sp_l - 3, part=(te - sp_l, max(r, sp_i / 2 + 0.05)))
        if f == 2:
            cur = tube(sp_i / 2, te - sp_l - 2.2, ri_to=te - sp_l - 3)
        lathe_frame(sc, [(coll2, CHUCK)], mesh(cur), 0.0, tools=[(blade.move((te - sp_l - 1.1, -r, 0)), TOOL)],
                    cam=cam2, step=7, title=f"Spacer: part off at {sp_l:.1f} mm",
                    caption=f"Part off {sp_l:.1f} mm long (+-0.05: it sets where the bearing pair sits), deburr both ends. "
                            "Make four.", hold=1.2, work_spins=False, steel=False)
    # 8: the stack on the axle as drawn: washer, spacer, 2 x 6202 (in the sprocket), circlip
    pose = lambda s, z0=0.0: solid(s).rotate((0, 0, 0), (0, 1, 0), 90).translate(cq.Vector(L_stem + z0, 0, 0))
    tp = mesh(pose(turned_part))
    parts_ = [(mesh(pose(washer)), DARKSTEEL, 0.0), (mesh(pose(spacer, 4.0)), ALU, 0.0)]
    parts_ += [(mesh(pose(brg, zc[0])), BEARING, 0.0), (mesh(pose(brg, zc[1])), BEARING, 0.0)]
    parts_ += [(mesh(pose(clip, g_at)), "#2c3e50", 0.0)]
    for i in range(7):
        sc.clear()
        sc.add(tp, STEEL, lw=0.9)
        sc.lines(helix_lines(1.0, L_stem - 0.8, 5.05, 1.5), "#30343a", 1.3)
        for k, (m, c, _) in enumerate(parts_):
            dx = 70 * (1 - ease(min(i, 5), 6)) * (1 + 0.3 * k)
            sc.add(m.move((dx, 0, 0)), c, lw=0.7)
        sc.camera((L_stem + 12, 0, 0), (0.35, -0.85, 0.45), 34)
        labels = [("M10 x 1.5 stem,\n0.8 chamfer", (6, 0, 5), (0.04, 0.24)),
                  ("22 x 4 washer\n= the shoulder", (L_stem + 2, 0, -11), (0.10, 0.76)),
                  (f"spacer {sp_i:.1f} x {sp_o:.0f} x {sp_l:.1f}\n(6061 tube)", (L_stem + 4 + sp_l / 2, 0, -sp_o / 2),
                   (0.36, 0.80)),
                  ("2 x 6202-2RS\n(in the sprocket)", (L_stem + zc[0] + 5.5, 0, 17.5), (0.50, 0.20)),
                  (f"DIN 471-15 circlip;\n{land:.1f} mm land beyond it", (L_stem + g_at + 0.5, 0, 10.4), (0.76, 0.32))] \
            if i == 6 else ()
        sc.grab(8, "The idler axle stack", f"Shoulder washer, spacer, the sprocket's two 6202s, circlip: the bearing pair "
                f"stands {prot:.1f} mm out of the sprocket hub, so the axle's end stays inside the tooth face. About 50 min "
                "per axle and spacer; make four.", hold=1 if i < 6 else 8, labels=labels)
    sc.save("pat_axle")


# ---------------------------------------------------------------------------------------------------------------
# 4 / 7 / 8. Saw cuts: keyed bar (both designs) and 2020 extrusion (v2)
# ---------------------------------------------------------------------------------------------------------------
def bandsaw_static():
    bed = box(-420, 140, -90, 90, -140, -40).fuse(box(-90, -12, 22, 60, -40, 22))     # bed + fixed vise jaw
    legs = box(-400, -370, -80, 80, -400, -140).fuse(box(100, 130, -80, 80, -400, -140))
    return bed.fuse(legs)


def bandsaw_head(zb):
    blade = box(-0.6, 0.6, -110, 110, zb, zb + 22)
    arm = box(-40, 40, -125, 125, zb + 22, zb + 70)
    wheels = cyl_x(80, -18, 18, y=-120, z=zb + 60).fuse(cyl_x(80, -18, 18, y=120, z=zb + 60))
    return blade, arm.fuse(wheels)


def saw_cuts():
    pieces = {}
    D = design("paternoster")
    pa, pb = solid(D.L.shape("shaft_idle")), solid(D.L.shape("shaft_drive"))
    la, lb = pa.BoundingBox().zlen, pb.BoundingBox().zlen
    pieces["pat"] = [(f"{la:.0f}", pa), (f"{lb:.0f} drive", pb)]
    D2 = design("chain-carousel-v2")
    L2 = D2.L
    va, vb = solid(L2.shape("shaft")), solid(L2.shape("shaft_drive"))
    lva, lvb = va.BoundingBox().zlen, vb.BoundingBox().zlen
    pieces["v2"] = [(f"{lva:.0f}", va)] * 3 + [(f"{lvb:.0f} drive", vb)]
    ext = {k: solid(L2.shape(k)) for k in ("ext_post", "ext_y", "ext_x", "ext_fork_post", "ext_vial_post")}
    ext_len = {k: v.BoundingBox().zlen for k, v in ext.items()}
    print("saw_cuts lengths:", {k: round(v, 2) for k, v in ext_len.items()},
          [round(p[1].BoundingBox().zlen, 2) for p in pieces["pat"] + pieces["v2"]], flush=True)
    sc = Scene("Saw cuts: 5/8 in keyed bar (both designs), 2020 extrusion (v2)", 5)
    stat = mesh(bandsaw_static(), tol=0.5)
    vise_front = mesh(box(-90, -12, -60, -12, -40, 22), tol=0.5)
    cam = ((170, -40, -30), (0.18, -0.85, 0.5), 300)
    bar_kind = lambda s: "ext" if s.BoundingBox().xlen > 17 else "bar"

    def lay_x(s):
        """Piece along z -> along +x from x = 0, centred on y = z = 0."""
        s = solid(s).rotate((0, 0, 0), (0, 1, 0), 90)
        bb = s.BoundingBox()
        return s.translate(cq.Vector(-bb.xmin, -bb.center.y, -bb.center.z))

    def stock(length, kind):
        if kind == "bar":
            return cyl_x(15.875 / 2, -length, 0)
        return lay_x(D2.PT.extrusion_2020(length)).translate(cq.Vector(-length, 0, 0))

    def frames_for(step, title, caption, cuts, stock_len, kind, done, key_cut=None):
        rem = stock_len
        for ci, (lab, piece) in enumerate(cuts):
            L = piece.BoundingBox().zlen
            pm = mesh(lay_x(piece), tol=0.1)
            for f, (zb, adv) in enumerate(((60, 0.0), (60, 1.0), (14, 1.0), (-12, 1.0), (60, 1.0))):
                sc.clear()
                sc.add(stat, "#56708a", lw=0.4)
                sc.add(vise_front, "#56708a", lw=0.4)
                sh = L * (1 - adv)
                if rem - L > 1:
                    sc.add(mesh(stock(rem - L - 1.5, kind), tol=0.2).move((-1.5 - sh, 0, 0)), STEEL if kind == "bar" else ALU,
                           lw=0.6)
                gone = f == 4
                sc.add(pm.move((-sh, -150 if gone else 0, -20 if gone else 0)),
                       STEEL if kind == "bar" else ALU, lw=0.8)
                stop = mesh(box(L + 0.5, L + 30, -30, 30, -20, 40), tol=0.5)
                sc.add(stop, "#d35400", lw=0.5)
                sc.add(mesh(cyl_x(6, 140, L + 0.5, y=0, z=-30)), DARKSTEEL, lw=0.4)
                bl, arm = bandsaw_head(zb)
                sc.add(mesh(bl), "#7f8c8d", lw=0.4)
                sc.add(mesh(arm, tol=0.5), "#56708a", lw=0.4)
                for k, (dl, dp) in enumerate(done[-6:]):
                    sc.add(dp.move((0, -200 - 22 * k, -60)), STEEL if dp.body.bounds[3] - dp.body.bounds[2] < 17 else ALU,
                           lw=0.5)
                sc.camera(*cam)
                sc.grab(step, title, caption.format(L=L), hold=1.0 if f < 4 else 1.4,
                        key=(key_cut == ci and f == 3))
            done.append((lab, pm))
            rem -= L + 1.5

    done = []
    cap_bar = ("5/8 in keyed 1018 (72 in bar): horizontal bandsaw, 10-14 TPI bimetal blade, middle speed (about 120 ft/min), "
               "coolant. Stop block at {L:.1f} mm (+-0.5). Then chamfer both ends 0.5 mm x 45 deg on the belt sander and "
               "file the keyway's burr so sprockets and bearings slide on.")
    frames_for(1, f"Paternoster: keyed bar, {la:.0f} + {lb:.0f} mm", cap_bar, pieces["pat"], 1828.8, "bar", done, key_cut=0)
    frames_for(2, f"Chain carousel v2: keyed bar, 3 x {lva:.0f} + 1 x {lvb:.0f} mm", cap_bar, pieces["v2"], 1828.8, "bar", done)
    cap_ext = ("VEVOR 1000 mm 2020 bars. Miter saw with a carbide non-ferrous blade (or the bandsaw's top speed), "
               "extrusion clamped, slow feed. Set the stop once and cut all four alike (+-0.3 mm). File the slot burrs. "
               "Now {L:.1f} mm.")
    E = ext_len
    frames_for(3, f"2020 posts: 4 x {E['ext_post']:.0f} mm, each offcut gives a {E['ext_y']:.0f} mm rail",
               cap_ext, [(f"{E['ext_post']:.0f} post", ext["ext_post"]), (f"{E['ext_y']:.0f} rail", ext["ext_y"])], 1000.0,
               "ext", done)
    frames_for(4, f"2020 long rails 4 x {E['ext_x']:.1f} mm (2 per bar); {E['ext_y']:.0f} + {E['ext_fork_post']:.0f} + "
               f"{E['ext_vial_post']:.0f}", cap_ext, [(f"{E['ext_x']:.1f} rail", ext["ext_x"])] * 2, 1000.0, "ext", done)
    # 5: the cut list
    sc.clear()
    rows = ([("Paternoster keyed bar", [p for p in pieces["pat"]])] +
            [("v2 keyed bar", pieces["v2"])] +
            [("v2 2020 (x4 each)", [(f"{E['ext_post']:.0f} post", ext["ext_post"]), (f"{E['ext_y']:.0f} rail", ext["ext_y"]),
                                    (f"{E['ext_x']:.1f} rail", ext["ext_x"])]),
             ("v2 2020 (x1 each)", [(f"{E['ext_y']:.0f} station", ext["ext_y"]),
                                    (f"{E['ext_fork_post']:.0f} fork post", ext["ext_fork_post"]),
                                    (f"{E['ext_vial_post']:.0f} vial post", ext["ext_vial_post"])])])
    meshes, labels = [], []
    y = 0.0
    for ri, (name, items) in enumerate(rows):
        x = 0.0
        for lab, pc in items:
            m = mesh(lay_x(pc), tol=0.2).move((x, y, 0))
            L = pc.BoundingBox().zlen
            meshes.append((m, STEEL if pc.BoundingBox().xlen < 17 else ALU))
            labels.append((lab, (x + L / 2, y, 12)))
            x += L + 25
        y -= 110
    for i in range(3):
        sc.clear()
        for m, c in meshes:
            sc.add(m, c, lw=0.6)
        sc.camera((860, -170, 0), (0.0, -0.3, 0.95), 470)
        labs = [(t, p, (0, 0)) for t, p in labels] if i == 2 else ()
        if labs:
            pts = sc.project([p for _, p, _ in labs])
            labs = [(t, p, (u / W + 0.0, v / H - 0.06)) for (t, p, _), (u, v) in zip(labs, pts)]
        sc.grab(5, "The cut list", f"Keyed bar (as drawn now): paternoster {la:.1f} + {lb:.1f} (one 72 in bar); v2 3 x "
                f"{lva:.1f} + {lvb:.1f} (one 72 in bar). 2020: 4 posts {E['ext_post']:.0f} (+{E['ext_y']:.0f} rail from each "
                f"offcut), 4 long rails {E['ext_x']:.1f}, station rail {E['ext_y']:.0f}, fork post {E['ext_fork_post']:.1f}, "
                f"vial post {E['ext_vial_post']:.1f} (7 bars of 10). About 1.5 h with deburring.", hold=1 if i < 2 else 8,
                labels=labs)
    sc.save("saw_cuts")


# ---------------------------------------------------------------------------------------------------------------
# 10. Both designs: laser-cut 2 mm steel armature tabs and U-yoke arms; countersink the tabs
# ---------------------------------------------------------------------------------------------------------------
def steel_tabs():
    D = design("chain-carousel-v2")
    P = D.P
    tab_sam = solid(D.L.shape("armature_tab"))
    arm = solid(D.L.shape("uyoke_arm"))
    D1 = design("paternoster")
    same = (abs(solid(D1.L.shape("armature_tab")).Volume() - tab_sam.Volume()) < 1e-3 and
            abs(solid(D1.L.shape("uyoke_arm")).Volume() - arm.Volume()) < 1e-3)
    print("steel_tabs: paternoster tab/arm identical to v2:", same, flush=True)
    # laser state: the tab without its countersinks (the cone is drilled afterwards)
    ring = None
    for x, y in P.ARMATURE_SCREWS:
        r_ = cyl_z(3.0, -20.0, -18.0, x=x, y=y).cut(cyl_z(1.7, -21, -17, x=x, y=y))
        ring = r_ if ring is None else ring.fuse(r_)
    tab_plain_sam = tab_sam.fuse(ring)
    flip = lambda s: solid(s).rotate((0, 0, 0), (1, 0, 0), 180)
    tab_plain = flat(flip(tab_plain_sam))
    tab = flat(flip(tab_sam))
    armf = flat(arm)
    tx, ty = tab_plain.BoundingBox().xlen, tab_plain.BoundingBox().ylen
    ax_, ay_ = armf.BoundingBox().xlen, armf.BoundingBox().ylen
    gap = 6.0
    parts, offs = [], []
    for k in range(25):
        r, c = divmod(k, 7)
        parts.append(tab_plain)
        offs.append((12 + c * (tx + gap) + tx / 2, 12 + r * (ty + gap) + ty / 2))
    y_arm = 12 + 4 * (ty + gap) + ay_ / 2
    for k in range(4):
        parts.append(armf)
        offs.append((12 + k * (ax_ + gap) + ax_ / 2, y_arm))
    sheet = (0.0, max(12 + 7 * (tx + gap), 12 + 4 * (ax_ + gap)) + 6, 0.0, y_arm + ay_ / 2 + 12)
    job = SheetJob(parts, offs, sheet, P.ARMATURE_T)
    sc = Scene("Both designs: 2 mm steel armature tabs (12 + 13) and U-yoke arms (2 + 2)", 4)
    cam = ((sheet[1] / 2, sheet[3] / 2 - 25, 0), (0.1, -0.6, 0.8), 140)
    noz = cached(("noz", False), lambda: nozzle(False))
    tbl = slat_table(*sheet, pitch=30)
    tblm = (mesh(tbl[0], tol=0.5), mesh(tbl[1], tol=0.5))
    state = job.sheet
    rows = {}
    for i, p in enumerate(job.parts):
        c = p.BoundingBox().center
        rows.setdefault(round(c.y), []).append(i)
    out_parts = []

    def draw(head, kerf, hold, title, cap, step, key=False):
        sc.clear()
        sc.add(tblm[0], SLAT, edges=False)
        sc.add(tblm[1], TABLE, lw=0.4)
        sc.add(mesh(state, tol=0.05), "#8a9097", lw=0.6)
        for p in out_parts:
            sc.add(mesh(p, tol=0.05), "#9da4ab", lw=0.6)
        for k in kerf:
            sc.lines(pv.lines_from_points(k), KERF, 2.0)
        sc.add(noz.move((head[0], head[1], P.ARMATURE_T + 1.5)), DARKSTEEL, lw=0.5)
        sc.camera(*cam)
        sc.grab(step, title, cap, hold=hold, key=key)

    cap1 = ("14 ga low-carbon steel, 1008/1010 CR (it must be magnetic: no stainless). The CAD says 2.0 mm; 14 ga is 1.9 mm "
            "(see README). 25 tabs, 4 arms on one 270 x 190 mm piece. SendCutSend: upload dxf/armature_tab and uyoke_arm.")
    draw((sheet[0] - 30, sheet[3] + 20), [], 4, "Load the sheet", cap1, 1)
    cap2 = ("Fiber laser, holes first then outlines: 3.4 mm (M3 clearance) and the arms' 4.1 mm stub-pin hole and two 3.4 mm. "
            "Laser holes come out +-0.1 mm: check the 4.1 hole on a 4 mm pin; ream 4.0 H8 if it binds.")
    for ri, yk in enumerate(sorted(rows)):
        idx = rows[yk]
        kerf = []
        for i in idx:
            b, p = job.blanks[i], job.parts[i]
            for h in b.cut(p).Solids():
                state = state.cut(h)
                kerf.append(job.hole_path(h, 24))
        hp = job.parts[idx[-1]].BoundingBox().center
        draw((hp.x, hp.y), kerf, 1.3, "Laser cut: holes, then outlines", cap2, 2)
        kerf = []
        for i in idx:
            state = state.cut(job.blanks[i])
            out_parts.append(job.parts[i])
            kerf.append(job.outlines[i])
        draw((hp.x, hp.y), kerf, 1.6, "Laser cut: holes, then outlines", cap2, 2, key=(ri == 2))
    # 3: countersink the two holes of each tab on the drill press (tab in a small vise)
    vise = mesh(box(-40, 40, -30, -14.2, -12, 1.2).fuse(box(-40, 40, 14.2, 30, -12, 1.2)).fuse(box(-40, 40, -30, 30, -22, -12)), tol=0.3)
    csk_tool = cached("csk", lambda: solid(cq.Workplane("XY").circle(0.1).workplane(offset=5.9).circle(6.0).loft())
                      .fuse(cyl_z(6.0, 5.9, 14)).fuse(cyl_z(3.0, 14, 50)))
    chuck = cached("jacobs", jacobs_chuck)
    # hole centres in the flat (flipped) tab, ordered to match ARMATURE_SCREWS (flip maps y -> -y; flat turns 90 deg)
    holes = [h.Center() for h in blank_of(tab_plain).cut(tab_plain).Solids()]
    cap3 = ("Drill press, 90 deg countersink, 300 rpm, depth stop. Sink until the screw head is flush to 0.05 mm below: the "
            "drawn 6.0 mm fits DIN 7991 heads; ISO 10642 heads need about 6.7 mm. The dock magnet face is only 0.15 mm "
            "away when docked and the heads overlap its rim. Check with the M3 x 6 FHCS and a straightedge.")
    cur = tab_plain_sam
    for hi, hc in enumerate(holes):
        for f, u in enumerate((0.0, 0.5, 1.0)):
            r_s = 1.7 + (3.0 - 1.7) * u
            x_s, y_s = P.ARMATURE_SCREWS[hi]
            st = cur.cut(cq.Solid.makeCone(r_s + 0.001, 0.0, r_s + 0.001, cq.Vector(x_s, y_s, -20.0 - 0.001),
                                           cq.Vector(0, 0, 1))) if u > 0 else cur
            stf = flat(flip(st))
            sc.clear()
            sc.add(vise, "#56708a", lw=0.4)
            sc.add(mesh(stf, tol=0.03), "#9da4ab", lw=0.8)
            ztip = P.ARMATURE_T - r_s if u > 0 else P.ARMATURE_T + 6
            sc.add(csk_tool.move((hc.x, hc.y, ztip)), DARKSTEEL, lw=0.5)
            sc.add(chuck.move((hc.x, hc.y, ztip + 50)), CHUCK, lw=0.5)
            sc.camera((0, 4, 4), (0.25, -0.5, 0.83), 36)
            sc.grab(3, f"Countersink the tab's M3 holes ({hi + 1} of 2)", cap3, hold=1.2 if f < 2 else 2)
            if f == 2:
                cur = st
    print("steel_tabs: countersunk tab vs CAD volume diff", round(abs(cur.Volume() - tab_sam.Volume()), 3), flush=True)
    tm, am = mesh(tab, tol=0.03), mesh(armf, tol=0.05)
    for i in range(5):
        sc.clear()
        sc.add(tm.move((-30, 0, 0)), "#9da4ab", lw=0.8)
        sc.add(am.move((30, 0, 0)), "#9da4ab", lw=0.8)
        sc.camera((5, 0, 0), (0.25, -0.6, 0.76), 45)
        labels = [("2 x 3.4 mm, 90 deg countersink\non the magnet side", (-30 + holes[0].x, holes[0].y, 2), (0.05, 0.25)),
                  ("4.1 mm: stub pin", (30 + armf.BoundingBox().xmax - 6 - armf.BoundingBox().center.x, 0, 2), (0.70, 0.25))] \
            if i == 4 else ()
        sc.grab(4, "Deburr and check", "Deburr both faces: a tab must lie dead flat (no burr standing proud) on a surface "
                "plate. Check: the M3 x 6 FHCS head is flush or just below; an arm's 4.1 hole takes a 4 mm pin; 3.4 mm "
                "holes on 10 mm centres. About 30 min of shop time for all 29.", hold=1 if i < 4 else 8, labels=labels)
    sc.save("steel_tabs")


# ---------------------------------------------------------------------------------------------------------------
# 11. Station: stub pins (lathe) and module 1's printed plate (drill press, heat-set inserts)
# ---------------------------------------------------------------------------------------------------------------
def stub_pin_plate():
    D = design("chain-carousel-v2")
    P, L = D.P, D.L
    pin = solid(L.shape("stub_pin"))
    pin_len = pin.BoundingBox().ylen                                 # 8.0
    gf = [f.BoundingBox() for f in pin.Faces() if f.geomType() == "CYLINDER" and abs(f.BoundingBox().xlen - 3.2) < 0.01]
    g0, g1 = min(b.ymin for b in gf), max(b.ymax for b in gf)       # groove 6.4 .. 7.04 from the pressed end
    sc = Scene("Station: 4 mm stub pins (2 per design) + module 1's printed plate", 6)
    coll = cached("collet4", lambda: collet_chuck(2.0))
    hold = [(coll, CHUCK)]
    xe = 14 + pin_len + 3.5
    cam = ((14, 0, 0), LATHE_DIR, 14)
    tip, holder = (mesh(m) for m in turning_tool())
    gw = g1 - g0
    gblade = cached(("gblade", round(gw, 3)), lambda: box(-gw / 2, gw / 2, -20, 0, -3, 3))
    pblade = cached("pblade", lambda: box(-0.75, 0.75, -20, 0, -4, 4))
    ga, gb = xe - (pin_len - g0), xe - (pin_len - g1)               # groove on the bar, the free end is the pin's outer end

    def rod(end, ch_end=0.0, groove=None, part=None):
        prof = [(-40, 0), (-40, 2.0)]
        if part is not None:
            p0, pr = part
            prof += [(p0 - 1.5, 2.0), (p0 - 1.5, pr), (p0, pr), (p0, 2.0)]
        if groove is not None:
            a_, b_, gr = groove
            prof += [(a_, 2.0), (a_, gr), (b_, gr), (b_, 2.0)]
        prof += [(end - ch_end, 2.0), (end, 2.0 - ch_end), (end, 0)]
        return turned(prof)

    spin = 0.0
    cap1 = ("4 mm h8 303 stainless rod (free-machining; not a hardened dowel, which HSS can't groove) in a 4 mm ER "
            "collet, 2000 rpm, 0.03 mm/rev. Face and chamfer the end 0.3 mm.")
    for f in range(3):
        lathe_frame(sc, hold, mesh(rod(xe, 0.3 * (f + 1) / 3), tol=0.01), spin,
                    tools=[(tip.move((xe, -1.7, 0)), CARBIDE), (holder.move((xe, -1.7, 0)), TOOL)], cam=cam, step=1,
                    title="Face and chamfer the 4 mm rod", caption=cap1, hold=1.3)
        spin += 33
    cap2 = (f"{gw:.2f} mm grooving insert (DIN 6799-3.2 groove), 600 rpm, slow feed, oil: to 3.2 mm across (-0.06/0), "
            f"{pin_len - g1:.2f} mm from the end, so a full-diameter wall stays outside the e-clip. Check: the clip snaps in "
            "and can't be pulled off.")
    for f in range(4):
        gr = 2.0 - 0.4 * (f + 1) / 4
        lathe_frame(sc, hold, mesh(rod(xe, 0.3, groove=(ga, gb, gr)), tol=0.01), spin,
                    tools=[(gblade.move(((ga + gb) / 2, -gr, 0)), TOOL)], cam=cam, step=2, title="Cut the e-clip groove",
                    caption=cap2, hold=1.3, key=(f == 3))
        spin += 33
    cap3 = (f"1.5 mm parting blade, 600 rpm, at {pin_len:.1f} mm + 0.3 mm to face. Flip, face to {pin_len:.1f} mm, chamfer "
            "0.3 mm. Make 6 (2 per design + 2 spare).")
    xp = xe - pin_len
    for f in range(4):
        pr = 2.0 - 1.9 * (f + 1) / 4
        lathe_frame(sc, hold, mesh(rod(xe, 0.3, groove=(ga, gb, 1.6), part=(xp, pr)), tol=0.01), spin,
                    tools=[(pblade.move((xp - 0.75, -pr, 0)), TOOL)], cam=cam, step=3, title=f"Part off at {pin_len:.1f} mm",
                    caption=cap3, hold=1.3)
        spin += 33
    # 4-6: module 1's existing plate: raw print from Sam's STEP -> CAD plate (hole, slot, two insert holes)
    raw = solid(L._read_step_parts(L.REF / "sam-oct13-mounting-plate-and-carriage.step")["Mounting Plate"])
    final = solid(L.shape("sam_mounting_plate"))
    (hx, hy), (sx, sy) = P.LOCPIN_XY
    zt = -18.0
    feats = [("hole", hx, hy, P.LOCPIN_HOLE / 2, 3.5), ("slot", sx, sy, P.LOCPIN_HOLE / 2, 3.5)]
    feats += [("insert", x, y, 2.0, 4.5) for x, y in P.ARMATURE_SCREWS]
    for x, y in P.ARMATURE_SCREWS:      # how much plastic is round the insert holes
        col = raw.intersect(cyl_z(0.05, -40, 40, x=x, y=y)).BoundingBox()
        edge = raw.intersect(box(x, x + 40, y - 0.05, y + 0.05, zt + 0.5, zt + 1.0)).BoundingBox()
        print(f"stub_pin_plate: insert hole at ({x},{y}): plate z {col.zmin:.2f}..{col.zmax:.2f} (thickness "
              f"{col.zmax - col.zmin:.2f}); material to +x edge {edge.xmax - x - 2.0:.2f} mm past the 4.0 hole", flush=True)
    flipm = lambda s: solid(s).rotate((0, 0, 0), (1, 0, 0), 180)     # underside up: (x, y, z) -> (x, -y, -z)
    cur = raw
    table, head, _ = drill_press(head_z=60.0, table_top=0.0, table_r=150)
    m_table, m_head = mesh(table, tol=0.3), mesh(head, tol=0.3)
    chuck = cached("jacobs", jacobs_chuck)
    drill42 = cached("drill42", lambda: twist_drill(4.2, 60, 30))
    bbf = flipm(raw).BoundingBox()
    lift = -bbf.zmin

    def plate_frame(state, at, z_tip, title, cap, step, tool="drill", hold=1.2, key=False, inserts=()):
        sc.clear()
        sc.add(m_table, TABLE, lw=0.4)
        sc.add(mesh(flipm(state), tol=0.08).move((-at[0], at[1], lift)), PETG_BLUE, lw=0.6)
        for (ix, iy, iz) in inserts:
            sc.add(mesh(cyl_z(2.3, 0, 4.0).cut(cyl_z(1.25, -1, 5))).move((ix - at[0], -iy + at[1], iz)), BRASS, lw=0.5)
        if tool == "drill":
            sc.add(drill42.rot("y", -90).move((0, 0, z_tip)), DARKSTEEL, lw=0.5)
            sc.add(chuck.move((0, 0, z_tip + 60)), CHUCK, lw=0.5)
        else:
            sc.add(mesh(cyl_z(2.0, 0, 6).fuse(cyl_z(4.5, 6, 40)).fuse(cyl_z(9, 40, 140))).move((0, 0, z_tip)), "#2c3e50", lw=0.5)
        sc.add(m_head, "#4f6b5a", lw=0.4)
        sc.camera((0, 10, 30), (0.4, -0.75, 0.55), 70)
        sc.grab(step, title, cap, hold=hold, key=key)

    top = bbf.zmax + lift
    cap4 = ("Module 1's existing plate, underside up on the drill press, located by a printed template on its outline. "
            "4.2 mm brad-point drill, 1500 rpm, depth stop at 3.5 mm. Locating hole at (30, 16); the 6 mm slot at (70, -16): "
            "drill both ends 1.8 mm apart and file the web out (the pin only slides along x).")
    cap5 = ("Two 4.0 mm holes, 4.5 mm deep, for M3 x 4 heat-set inserts at (94, +-10) (Sam's frame) under the steel tab.")
    for fi, (kind, x, y, r, d) in enumerate(feats):
        plunges = [(x - 0.9, y), (x + 0.9, y)] if kind == "slot" else [(x, y)]
        for (px, py) in plunges:
            for f, dz in enumerate((15.0, -d)):
                if f == 1:
                    cur = cur.cut(cyl_z(r, zt - 1, zt + d, x=px, y=py))
                plate_frame(cur, (px, py), top + dz, "Drill the locating hole and slot" if kind != "insert" else
                            "Drill the insert holes", cap4 if kind != "insert" else cap5, 4 if kind != "insert" else 5,
                            key=(fi == 1 and f == 1))
        if kind == "slot":
            cur = cur.cut(cq.Workplane("XY").center(x, y).slot2D(P.LOCPIN_SLOT, P.LOCPIN_HOLE, 0).extrude(d + 1)
                          .translate((0, 0, zt - 1)).val())
    print("stub_pin_plate: drilled plate vs CAD volume diff", round(abs(cur.Volume() - final.Volume()), 2), flush=True)
    ins = []
    cap6 = ("Soldering iron with an M3 insert tip at 230-245 C (PETG), straight down until flush, then press flat with a "
            "cold steel block. Check: an M3 x 6 flat head pulls the tab down without spinning the insert.")
    for k, (x, y) in enumerate(P.ARMATURE_SCREWS):
        for f, dz in enumerate((14.0, 4.0, 0.0)):
            iz = top - 4.0 + dz * 0.5 if f < 2 else top - 4.0
            plate_frame(final, (x, y), iz + 4.0, f"Set the M3 heat-set inserts ({k + 1} of 2)", cap6, 6, tool="iron",
                        inserts=ins + [(x, y, iz)], hold=1.2 if f < 2 else 1.8)
        ins.append((x, y, top - 4.0))
    sc.save("stub_pin_plate")


# ---------------------------------------------------------------------------------------------------------------
# 12 (optional). Paternoster: break the #35 roll into 9-pitch segments, join them with SA-1 connecting links
# ---------------------------------------------------------------------------------------------------------------
def chain_break():
    D = design("paternoster")
    P, PT = D.P, D.PT
    inner = mesh(solid(PT.chain_inner_link()), tol=0.02)
    outer_s = solid(PT.chain_outer_link(clip=False))
    outer = mesh(outer_s, tol=0.02)
    pin_len = outer_s.BoundingBox().zlen
    pin = cyl_z(P.PIN_D / 2, -pin_len / 2, pin_len / 2)
    outer_nopin = mesh(outer_s.cut(cyl_z(P.PIN_D / 2 + 0.01, -20, 20, x=-P.P / 2)), tol=0.02)
    pin_m = mesh(pin.translate(cq.Vector(-P.P / 2, 0, 0)), tol=0.02)
    sa1 = mesh(solid(PT.chain_sa1_link()), tol=0.02)
    seg_n = P.MODULE_LINKS - 1
    sc = Scene("Paternoster: #35 chain into 9-pitch segments + SA-1 links (x2 loops)", 4)
    k_break = seg_n + 1                      # the outer link whose left pin comes out
    cam = ((k_break * P.P - 30, 0, 0), (0.25, -0.6, 0.76), 42)
    bench = mesh(box(-40, 200, -60, 60, -12, -6), tol=1)

    def links(skip=None, shift_right=0.0, shade=()):
        out = []
        for k in range(0, 15):
            x = k * P.P + (shift_right if k >= k_break else 0.0)
            if k == skip:
                continue
            m = (outer if k % 2 == 0 else inner).move((x, 0, 0))
            out.append((m, "#4b7bd8" if k in shade else "#8a939c"))
        return out

    def breaker(zp):
        x = k_break * P.P - P.P / 2
        base = box(x - 12, x + 12, -14, 14, -26, -6.2).cut(cyl_z(2.5, -30, 0, x=x))
        frame = box(x - 10, x + 10, 14, 24, -26, 40).fuse(box(x - 10, x + 10, -6, 24, 30, 40))
        screw = cyl_z(5, zp + 14, zp + 60, x=x).fuse(cyl_z(1.6, zp, zp + 14, x=x))
        handle = cyl_x(2.5, x - 30, x + 30, z=zp + 60)
        return [(mesh(base.fuse(frame), tol=0.3), "#a83232"), (mesh(screw.fuse(handle), tol=0.1), DARKSTEEL)]

    seg = tuple(range(1, seg_n + 1))
    cap1 = (f"Each loop is 12 x ({seg_n} plain pitches + 1 SA-1 connecting link) = {P.N_LINKS} links. Cut 24 segments of "
            f"{seg_n} pitches from the 10 ft roll (216 pitches). A segment must start and end on an inner (bushing) link, so "
            "the SA-1 link's pins can join two of them.")
    for i in range(3):
        sc.clear()
        sc.add(bench, BENCH, lw=0.3)
        for m, c in links(shade=seg):
            sc.add(m, c, lw=0.5)
        sc.camera(*cam)
        sc.grab(1, f"Count {seg_n} pitches", cap1, hold=1.5 if i < 2 else 4)
    cap2 = ("Chain breaker (#25-#60, Surplus Center 100115) with the #35 anvil under the link. Centre the punch on the pin "
            "of the outer link just past the segment and screw it down until the pin is out. If the riveted head won't "
            "start, grind it flush first. Rivet pins aren't reused.")
    top = pin_len / 2
    for f in range(7):
        dz = -(pin_len + 2) * ease(f, 7)
        sc.clear()
        sc.add(bench.move((0, 0, -20)), BENCH, lw=0.3)
        for m, c in links(skip=k_break, shade=seg):
            sc.add(m, c, lw=0.5)
        sc.add(outer_nopin.move((k_break * P.P, 0, 0)), "#8a939c", lw=0.5)
        sc.add(pin_m.move((k_break * P.P, 0, dz)), "#d35400", lw=0.6)
        for m, c in breaker(top + dz + 0.2):
            sc.add(m, c, lw=0.5)
        sc.camera(*cam)
        sc.grab(2, "Push the pin out", cap2, hold=1.2, key=(f == 4))
    cap3 = ("The segment comes away with an inner link at each end. Repeat at the other end; 24 segments for both "
            "loops. Check: count the rollers (bushings), and lay segments side by side: all the same length.")
    for f in range(4):
        sc.clear()
        sc.add(bench, BENCH, lw=0.3)
        for m, c in links(skip=k_break, shift_right=25 * ease(f, 4), shade=seg):
            sc.add(m, c, lw=0.5)
        sc.add(outer_nopin.move((k_break * P.P + 25 * ease(f, 4), 0, 0)), "#8a939c", lw=0.5)
        sc.camera(*cam)
        sc.grab(3, "Lift the segment out", cap3, hold=1.2 if f < 3 else 2.5)
    cap4 = ("Join two segments with an SA-1 connecting link (McMaster 7321K31): pins through both end bushings, tab plate "
            "on the gondola side, tab pointing out of the loop; the free plate and the spring clip go on the other side, "
            "clip's closed end leading in the direction of travel.")
    for f in range(5):
        sc.clear()
        sc.add(bench, BENCH, lw=0.3)
        for k in range(1, seg_n + 1):
            sc.add((outer if k % 2 == 0 else inner).move((k * P.P, 0, 0)), "#4b7bd8", lw=0.5)
        for k in range(1, 5):
            kk = k_break + k
            sc.add((outer if kk % 2 == 0 else inner).move((kk * P.P, 0, 0)), "#4b7bd8", lw=0.5)
        z = 25 * (1 - ease(f, 5))
        sc.add(sa1.move((k_break * P.P, 0, z)), "#c0392b", lw=0.6)
        sc.camera(*cam)
        sc.grab(4, "Join with an SA-1 connecting link", cap4, hold=1.2 if f < 4 else 8)
    sc.save("chain_break")


# === main ===
ORDER = ["pat_plates", "v2_plates", "pat_sprocket", "pinion", "v2_sprocket", "pat_axle", "steel_tabs", "stub_pin_plate",
         "saw_cuts", "chain_break"]


def contact_sheet():
    names = [n for n in ORDER if (OUT / f"{n}_key.png").exists()]
    cols = 3
    rows = math.ceil(len(names) / cols)
    tw, th = 450, 253
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 8, rows * (th + 26) + (rows + 1) * 8 + 40), "white")
    d = ImageDraw.Draw(sheet)
    d.text((10, 10), "Shop processes for the paternoster and chain carousel v2 (cad/shop/anim, one GIF + MP4 each)",
           font=font(18, "-Bold"), fill=INK)
    for k, n in enumerate(names):
        im = Image.open(OUT / f"{n}_key.png").resize((tw, th), Image.LANCZOS)
        x, y = 8 + (k % cols) * (tw + 8), 48 + (k // cols) * (th + 34)
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + tw - 1, y + th - 1], outline=(190, 195, 200))
        d.text((x + 2, y + th + 4), f"{k + 1}. {n}.gif", font=font(14), fill=INK2)
    sheet.save(HERE / "shop_processes.png")
    print("wrote shop_processes.png", len(names))


if __name__ == "__main__":
    args = sys.argv[1:] or ["all"]
    if args == ["sheet"]:
        contact_sheet()
        sys.exit()
    for name in (ORDER if args == ["all"] else args):
        t0 = time.time()
        globals()[name]()
        print(f"{name}: {time.time() - t0:.0f} s", flush=True)
