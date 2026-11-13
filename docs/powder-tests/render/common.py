"""Shared helpers for the powder-test animations.

Every scene script builds its apparatus from simple solids, moves it frame by frame,
and hands each rendered frame to `Movie`, which adds the title card, step caption,
part labels, readouts and a live chart, then encodes MP4 and GIF with ffmpeg.

Units are millimetres and seconds. Geometry is illustrative: proportions follow the
standards where they fix them (orifice sizes, cup volumes, sieve diameters), the rest
is drawn to look like typical commercial apparatus.
"""
from __future__ import annotations

import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pyvista as pv  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "animations"
W, H = 1280, 720
FPS = 24
GIF_MAX = 4_800_000    # bytes; GitHub's camo proxy refuses images over 5 MiB
G_VIS = 9810.0 / 14.0  # "visual" gravity (mm/s^2) so falling grains stay on screen for a few frames

_FONT_DIR = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf"


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSansMono" if mono else "DejaVuSans"
    if bold:
        name += "-Bold"
    return ImageFont.truetype(str(_FONT_DIR / f"{name}.ttf"), size)


# --------------------------------------------------------------------------- colours / materials
C = dict(
    steel="#b7bec7", steel_dark="#7d858f", brass="#c9a24c", alu="#cdd3db", glass="#cfe5fb",
    dark="#2f343b", mid="#5b626b", light="#eef1f4", white="#fbfbfa", bench="#d9cfbf",
    powder="#8e949b", salt="#ece6da", rubber="#2b2b2b", orange="#e07a1f", blue="#2f6db5",
    red="#cf3a2f", green="#3a9a5b", lcd="#1c2a22", lamp="#ffb347", laser="#ff2a1a",
)

MAT = {
    "steel": dict(color=C["steel"], specular=0.9, specular_power=45, diffuse=0.75, ambient=0.18),
    "steel_dark": dict(color=C["steel_dark"], specular=0.7, specular_power=35, diffuse=0.75, ambient=0.15),
    "brass": dict(color=C["brass"], specular=0.8, specular_power=40, diffuse=0.8, ambient=0.18),
    "alu": dict(color=C["alu"], specular=0.6, specular_power=30, diffuse=0.8, ambient=0.2),
    "glass": dict(color=C["glass"], opacity=0.28, specular=1.0, specular_power=90, diffuse=0.5, ambient=0.25),
    "dark": dict(color=C["dark"], specular=0.35, specular_power=20, diffuse=0.8, ambient=0.15),
    "mid": dict(color=C["mid"], specular=0.3, specular_power=20, diffuse=0.8, ambient=0.15),
    "light": dict(color=C["light"], specular=0.25, specular_power=15, diffuse=0.85, ambient=0.2),
    "white": dict(color=C["white"], specular=0.2, specular_power=15, diffuse=0.85, ambient=0.22),
    "bench": dict(color=C["bench"], specular=0.1, specular_power=10, diffuse=0.85, ambient=0.25),
    "rubber": dict(color=C["rubber"], specular=0.1, specular_power=10, diffuse=0.8, ambient=0.15),
    "powder": dict(color=C["powder"], specular=0.15, specular_power=10, diffuse=0.9, ambient=0.2),
    "salt": dict(color=C["salt"], specular=0.1, specular_power=10, diffuse=0.9, ambient=0.25),
    "orange": dict(color=C["orange"], specular=0.4, specular_power=20, diffuse=0.8, ambient=0.2),
    "blue": dict(color=C["blue"], specular=0.4, specular_power=20, diffuse=0.8, ambient=0.2),
    "red": dict(color=C["red"], specular=0.4, specular_power=20, diffuse=0.8, ambient=0.2),
    "green": dict(color=C["green"], specular=0.4, specular_power=20, diffuse=0.8, ambient=0.2),
    "lcd": dict(color=C["lcd"], specular=0.6, specular_power=60, diffuse=0.6, ambient=0.2),
}


def hex_rgb(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


# --------------------------------------------------------------------------- easing / timeline
def clamp01(x):
    return np.clip(x, 0.0, 1.0)


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ramp(t, t0, t1):
    """0 before t0, 1 after t1, smoothstep between."""
    if t1 <= t0:
        return float(t >= t1)
    return float(smooth((t - t0) / (t1 - t0)))


def lin(t, t0, t1):
    if t1 <= t0:
        return float(t >= t1)
    return float(clamp01((t - t0) / (t1 - t0)))


def lerp(a, b, s):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    return a + (b - a) * s


@dataclass
class Step:
    t0: float
    t1: float
    text: str


@dataclass
class Timeline:
    steps: list[Step]

    @property
    def duration(self) -> float:
        return self.steps[-1].t1

    def current(self, t: float) -> tuple[int, Step]:
        for i, s in enumerate(self.steps):
            if s.t0 <= t < s.t1:
                return i, s
        return len(self.steps) - 1, self.steps[-1]


# --------------------------------------------------------------------------- geometry
def lathe(profile, res: int = 96, a0: float = 0.0, a1: float = 360.0, closed: bool = True,
          feature_angle: float = 40.0) -> pv.PolyData:
    """Surface of revolution about +z from an (r, z) polyline.

    closed=True treats the profile as a loop (a solid wall); a0/a1 < 360 makes a cutaway,
    with the cut faces capped when the profile is closed.
    """
    rz = np.asarray(profile, float)
    n = len(rz)
    full = abs((a1 - a0) - 360.0) < 1e-6
    na = res if full else max(4, int(res * (a1 - a0) / 360.0)) + 1
    th = np.radians(np.linspace(a0, a1, na, endpoint=not full))
    pts = np.empty((na * n, 3))
    for i, t in enumerate(th):
        pts[i * n:(i + 1) * n, 0] = rz[:, 0] * math.cos(t)
        pts[i * n:(i + 1) * n, 1] = rz[:, 0] * math.sin(t)
        pts[i * n:(i + 1) * n, 2] = rz[:, 1]
    faces = []
    m = n if closed else n - 1
    rings = na if full else na - 1
    for i in range(rings):
        i2 = (i + 1) % na
        for j in range(m):
            j2 = (j + 1) % n
            faces.append((4, i * n + j, i * n + j2, i2 * n + j2, i2 * n + j))
    mesh = pv.PolyData(pts, np.array(faces, dtype=np.int64).ravel())
    if closed and not full:
        for t in (th[0], th[-1]):
            poly = np.c_[rz[:, 0] * math.cos(t), rz[:, 0] * math.sin(t), rz[:, 1]]
            cap = pv.PolyData(poly, np.r_[n, np.arange(n)]).triangulate()
            mesh = mesh.merge(cap)
    mesh = mesh.clean(tolerance=1e-9)
    return mesh.compute_normals(auto_orient_normals=closed and full, consistent_normals=True,
                                split_vertices=True, feature_angle=feature_angle)


def tube(r_in, r_out, z0, z1, **kw) -> pv.PolyData:
    return lathe([(r_in, z0), (r_out, z0), (r_out, z1), (r_in, z1)], **kw)


def disc(r, z0, z1, **kw) -> pv.PolyData:
    return lathe([(0, z0), (r, z0), (r, z1), (0, z1)], **kw)


def box(xmin, xmax, ymin, ymax, zmin, zmax) -> pv.PolyData:
    return pv.Box(bounds=(xmin, xmax, ymin, ymax, zmin, zmax)).triangulate().compute_normals(
        split_vertices=True, feature_angle=30)


def cbox(center, size) -> pv.PolyData:
    c = np.asarray(center, float)
    s = np.asarray(size, float) / 2
    return box(c[0] - s[0], c[0] + s[0], c[1] - s[1], c[1] + s[1], c[2] - s[2], c[2] + s[2])


def rod(p0, p1, r, res=32) -> pv.PolyData:
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    return pv.Cylinder(center=(p0 + p1) / 2, direction=d / L, radius=r, height=L,
                       resolution=res).triangulate().compute_normals(split_vertices=True, feature_angle=40)


def polar_surface(zfun, r_max, r_min=0.0, nr=36, nth=96, a0=0.0, a1=360.0) -> pv.PolyData:
    """Height field z = zfun(r, theta) over an annulus (powder free surfaces)."""
    full = abs((a1 - a0) - 360.0) < 1e-6
    th = np.radians(np.linspace(a0, a1, nth + (0 if full else 1), endpoint=not full))
    rr = np.linspace(r_min, r_max, nr)
    R, T = np.meshgrid(rr, th, indexing="ij")
    Z = zfun(R, T)
    pts = np.c_[(R * np.cos(T)).ravel(), (R * np.sin(T)).ravel(), np.asarray(Z).ravel()]
    nt = len(th)
    faces = []
    for i in range(nr - 1):
        for j in range(nt if full else nt - 1):
            j2 = (j + 1) % nt
            faces.append((4, i * nt + j, i * nt + j2, (i + 1) * nt + j2, (i + 1) * nt + j))
    m = pv.PolyData(pts, np.array(faces, dtype=np.int64).ravel()).clean(tolerance=1e-9)
    return m.compute_normals(consistent_normals=True, auto_orient_normals=False, split_vertices=False)


def heap_apex(volume, R, tan_t):
    """Apex height of a conical heap (slope tan_t) holding `volume` in a cylinder of radius R."""
    if volume <= 0:
        return 0.0
    a = (3.0 * volume * tan_t ** 2 / math.pi) ** (1.0 / 3.0)
    if a <= R * tan_t:
        return a
    return (volume + (2.0 / 3.0) * math.pi * R ** 3 * tan_t) / (math.pi * R ** 2)


def heap_z(r, apex, tan_t, floor=0.0):
    return np.maximum(floor, floor + apex - r * tan_t)


def matrix(translate=(0, 0, 0), rot_deg=0.0, axis=(0, 0, 1), origin=(0, 0, 0), scale=1.0) -> np.ndarray:
    """4x4: rotate about `axis` through `origin`, scale, then translate."""
    ax = np.asarray(axis, float)
    ax = ax / np.linalg.norm(ax)
    a = math.radians(rot_deg)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    Rm = np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K
    o = np.asarray(origin, float)
    M = np.eye(4)
    M[:3, :3] = Rm * scale
    M[:3, 3] = o - (Rm * scale) @ o + np.asarray(translate, float)
    return M


# --------------------------------------------------------------------------- particles
def grain_colors(n, base, spread=0.10, seed=0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    b = hex_rgb(base)
    f = 1.0 + rng.normal(0, spread, n)
    return np.clip(b[None, :] * f[:, None], 0, 255).astype(np.uint8)


def stream(t, t_start, t_end, rate, origin, r_spread, v0=60.0, g=G_VIS, floor=None, seed=1,
           lateral=0.0, max_fall=1e9):
    """Positions of grains in a free-falling stream that is emitted from `origin` between
    t_start and t_end at `rate` grains/s. floor(x, y) gives the landing height. Deterministic."""
    origin = np.asarray(origin, float)
    if t <= t_start:
        return np.empty((0, 3)), np.empty(0, int)
    i_last = int(min(t, t_end) * rate - t_start * rate)
    t_fall = (-v0 + math.sqrt(v0 * v0 + 2 * g * max_fall)) / g
    i_first = max(0, int((t - t_start - t_fall * 1.05) * rate) - 2)
    if i_last <= i_first:
        return np.empty((0, 3)), np.empty(0, int)
    idx = np.arange(i_first, i_last)
    rng = np.random.default_rng(seed)
    big = rng.random((max(i_last, 1) + 1, 4))
    u = big[idx]
    te = t_start + idx / rate
    tau = t - te
    rr = r_spread * np.sqrt(u[:, 0])
    ph = 2 * np.pi * u[:, 1]
    x = origin[0] + rr * np.cos(ph) + lateral * (u[:, 2] - 0.5) * tau
    y = origin[1] + rr * np.sin(ph) + lateral * (u[:, 3] - 0.5) * tau
    z = origin[2] - v0 * tau - 0.5 * g * tau ** 2
    pts = np.c_[x, y, z]
    keep = z > origin[2] - max_fall
    if floor is not None:
        keep &= z > floor(x, y)
    return pts[keep], idx[keep]


def surface_grains(n, r_max, zfun, r_min=0.0, a0=0.0, a1=360.0, seed=3, lift=0.15):
    """Fixed random grains scattered over a height field; zfun(r, theta) moves them with the surface."""
    rng = np.random.default_rng(seed)
    r = np.sqrt(rng.uniform((r_min / r_max) ** 2 if r_max > 0 else 0, 1, n)) * r_max
    th = np.radians(rng.uniform(a0, a1, n))

    def at(*args, **kw):
        z = zfun(r, th, *args, **kw) + lift
        return np.c_[r * np.cos(th), r * np.sin(th), z]
    return at


# --------------------------------------------------------------------------- 3D stage
class Stage:
    def __init__(self, ssao_radius=None, bench=(-260, 260, -170, 170), bench_color="bench",
                 bg=("#f5f7fa", "#c4d1e2"), w=W, h=H):
        self.pl = pv.Plotter(off_screen=True, window_size=(w, h), lighting="none")
        self.pl.set_background(bg[0], top=bg[1])
        self.w, self.h = w, h
        self.names: set[str] = set()
        if bench is not None:
            x0, x1, y0, y1 = bench
            self.add("bench", box(x0, x1, y0, y1, -25, 0), bench_color)
        key = pv.Light(position=(350, -420, 650), focal_point=(0, 0, 40), intensity=0.72, light_type="scene light")
        fill = pv.Light(position=(-500, -260, 300), focal_point=(0, 0, 40), intensity=0.38, light_type="scene light")
        rim = pv.Light(position=(-80, 520, 420), focal_point=(0, 0, 40), intensity=0.32, light_type="scene light")
        head = pv.Light(light_type="headlight", intensity=0.14)
        for L in (key, fill, rim, head):
            self.pl.add_light(L)
        self.pl.enable_depth_peeling(6)
        # SSAO streaks on thin transparent walls under llvmpipe, so contact shadows are faked
        # with soft decals (`shadow`) instead.
        self.pl.enable_anti_aliasing("fxaa")
        self._shadow_tex = None

    def add(self, name, mesh, mat="steel", **kw):
        style = dict(MAT[mat]) if isinstance(mat, str) else dict(mat)
        style.update(kw)
        if mesh is None or mesh.n_points == 0:
            self.remove(name)
            return None
        a = self.pl.add_mesh(mesh, name=name, smooth_shading=True, show_scalar_bar=False, **style)
        self.names.add(name)
        return a

    def grains(self, name, pts, colors=None, size=4.0, mat="powder"):
        pts = np.asarray(pts, float).reshape(-1, 3)
        if len(pts) == 0:
            self.remove(name)
            return None
        cloud = pv.PolyData(pts)
        style = dict(MAT[mat])
        style.pop("color", None) if colors is not None else None
        if colors is not None:
            cloud["rgb"] = np.asarray(colors, np.uint8)[: len(pts)]
            a = self.pl.add_mesh(cloud, name=name, scalars="rgb", rgb=True, render_points_as_spheres=True,
                                 point_size=size, show_scalar_bar=False, **style)
        else:
            a = self.pl.add_mesh(cloud, name=name, render_points_as_spheres=True, point_size=size, **style)
        self.names.add(name)
        return a

    def shadow(self, name, center, rx, ry=None, strength=0.45, z=0.06):
        """Soft elliptical contact shadow on the bench (a textured quad)."""
        ry = rx if ry is None else ry
        if self._shadow_tex is None:
            n = 128
            yy, xx = np.mgrid[-1:1:n * 1j, -1:1:n * 1j]
            rr = np.sqrt(xx ** 2 + yy ** 2)
            a = np.clip(1 - rr, 0, 1) ** 1.6
            rgba = np.zeros((n, n, 4), np.uint8)
            rgba[..., 3] = (255 * a).astype(np.uint8)
            self._shadow_tex = pv.Texture(rgba)
        quad = pv.Plane(center=(center[0], center[1], z), i_size=2 * rx, j_size=2 * ry)
        quad.texture_map_to_plane(inplace=True)
        a = self.pl.add_mesh(quad, name=name, texture=self._shadow_tex, opacity=strength, lighting=False,
                             show_scalar_bar=False)
        self.names.add(name)
        return a

    def remove(self, name):
        if name in self.names:
            self.pl.remove_actor(name, render=False)
            self.names.discard(name)

    def pose(self, name, M=None, visible=True, opacity=None):
        a = self.pl.actors.get(name)
        if a is None:
            return
        if M is not None:
            a.user_matrix = M
        a.SetVisibility(bool(visible))
        if opacity is not None:
            a.prop.opacity = float(opacity)

    def camera(self, pos, focal, up=(0, 0, 1), view_angle=30.0):
        self.pl.camera_position = [tuple(pos), tuple(focal), tuple(up)]
        self.pl.camera.view_angle = view_angle
        self.pl.camera.clipping_range = (5, 5000)

    def orbit(self, focal, dist, azim_deg, elev_deg, view_angle=30.0):
        a = math.radians(azim_deg)
        e = math.radians(elev_deg)
        f = np.asarray(focal, float)
        pos = f + dist * np.array([math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e)])
        self.camera(pos, f, view_angle=view_angle)

    def project(self, xyz):
        """World point -> (x, y) pixels from the top-left, for labels."""
        ren = self.pl.renderer
        ren.SetWorldPoint(float(xyz[0]), float(xyz[1]), float(xyz[2]), 1.0)
        ren.WorldToDisplay()
        x, y, _ = ren.GetDisplayPoint()
        return x, self.h - y

    def render(self) -> np.ndarray:
        self.pl.render()
        return np.asarray(self.pl.screenshot(return_img=True))[:, :, :3]


# --------------------------------------------------------------------------- 2D overlay
def _rrect(draw, box, r, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


@dataclass
class Label:
    text: str
    anchor: tuple            # world xyz
    offset: tuple            # pixel offset of the label box from the anchor
    alpha: float = 1.0


@dataclass
class Readout:
    title: str
    value: str
    color: str = "#7CFC9A"


class Chart:
    """A matplotlib panel redrawn every frame; `draw(fn)` calls fn(fig, ax) on a fresh axes."""

    def __init__(self, w_px=470, h_px=300, dpi=100):
        self.fig = plt.figure(figsize=(w_px / dpi, h_px / dpi), dpi=dpi)
        self.fig.patch.set_alpha(0.0)
        self.w, self.h = w_px, h_px

    def draw(self, fn) -> Image.Image:
        self.fig.clf()
        fn(self.fig)
        self.fig.canvas.draw()
        buf = np.asarray(self.fig.canvas.buffer_rgba()).copy()
        return Image.fromarray(buf, "RGBA")


def style_axes(ax, title=None):
    ax.set_facecolor((1, 1, 1, 0))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#555")
    ax.tick_params(labelsize=8.5, colors="#333")
    ax.xaxis.label.set_size(9.5)
    ax.yaxis.label.set_size(9.5)
    ax.grid(alpha=0.25, lw=0.6)
    if title:
        ax.set_title(title, fontsize=10.5, loc="left", color="#222", fontweight="bold")


@dataclass
class Overlay:
    title: str
    subtitle: str
    badge: str
    badge2: str = ""
    labels: list = field(default_factory=list)
    readouts: list = field(default_factory=list)
    chart: Image.Image | None = None
    chart_pos: tuple = (W - 500, 84)
    step_idx: int = 0
    n_steps: int = 1
    step_text: str = ""
    speed_note: str = ""
    footer: str = ""
    readout_y: float | None = None
    readout_row_px: float = 520.0


def compose(rgb: np.ndarray, ov: Overlay, stage: Stage | None = None) -> Image.Image:
    img = Image.fromarray(rgb).convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # title card
    f_t, f_s, f_b = font(27, bold=True), font(16), font(15, bold=True)
    tw = max(d.textlength(ov.title, font=f_t), d.textlength(ov.subtitle, font=f_s)) + 36
    _rrect(d, (16, 14, 16 + tw, 104), 12, (255, 255, 255, 228), outline=(0, 0, 0, 30))
    d.text((34, 22), ov.title, font=f_t, fill=(25, 28, 33, 255))
    d.text((34, 56), ov.subtitle, font=f_s, fill=(70, 76, 84, 255))
    bx = 34
    for b, col in ((ov.badge, (47, 109, 181, 255)), (ov.badge2, (224, 122, 31, 255))):
        if not b:
            continue
        bw = d.textlength(b, font=f_b) + 18
        _rrect(d, (bx, 78, bx + bw, 99), 9, col)
        d.text((bx + 9, 80), b, font=f_b, fill=(255, 255, 255, 255))
        bx += bw + 8
    # labels with leader lines
    f_l = font(15, bold=True)
    for lb in ov.labels:
        if lb.alpha <= 0.01 or stage is None:
            continue
        ax_, ay_ = stage.project(lb.anchor)
        lx, ly = ax_ + lb.offset[0], ay_ + lb.offset[1]
        a = int(255 * lb.alpha)
        tw_ = d.textlength(lb.text, font=f_l)
        bx0 = lx - (tw_ + 16 if lb.offset[0] < 0 else 0)
        d.line((ax_, ay_, lx, ly), fill=(30, 34, 40, int(0.85 * a)), width=2)
        d.ellipse((ax_ - 4, ay_ - 4, ax_ + 4, ay_ + 4), fill=(224, 122, 31, a))
        _rrect(d, (bx0, ly - 13, bx0 + tw_ + 16, ly + 13), 7, (255, 255, 255, int(0.93 * a)),
               outline=(30, 34, 40, int(0.4 * a)))
        d.text((bx0 + 8, ly - 10), lb.text, font=f_l, fill=(25, 28, 33, a))
    # chart panel
    if ov.chart is not None:
        cx, cy = ov.chart_pos
        cw, ch = ov.chart.size
        _rrect(d, (cx - 10, cy - 8, cx + cw + 6, cy + ch + 6), 12, (255, 255, 255, 222), outline=(0, 0, 0, 30))
    # readouts: right-aligned rows under the chart, wrapping at READOUT_ROW_PX
    f_rt, f_rv = font(13, bold=True), font(24, bold=True, mono=True)
    ry = ov.readout_y if ov.readout_y is not None else (
        ov.chart_pos[1] + (ov.chart.size[1] if ov.chart is not None else 0) + 18)
    rows, row, row_w = [], [], 0.0
    for ro in ov.readouts:
        rw = max(d.textlength(ro.value, font=f_rv), d.textlength(ro.title, font=f_rt)) + 26
        if row and row_w + rw > ov.readout_row_px:
            rows.append(row)
            row, row_w = [], 0.0
        row.append((ro, rw))
        row_w += rw + 10
    if row:
        rows.append(row)
    for r_i, row in enumerate(rows):
        rx = W - 16
        y = ry + r_i * 68
        for ro, rw in reversed(row):
            _rrect(d, (rx - rw, y, rx, y + 60), 10, (22, 30, 26, 235))
            d.text((rx - rw + 13, y + 6), ro.title, font=f_rt, fill=(180, 196, 186, 255))
            d.text((rx - rw + 13, y + 24), ro.value, font=f_rv,
                   fill=tuple(hex_rgb(ro.color).astype(int).tolist() + [255]))
            rx -= rw + 10
    # step caption
    if ov.step_text:
        f_k, f_c = font(14, bold=True), font(21)
        cap = ov.step_text
        cw_ = d.textlength(cap, font=f_c) + 40
        y0 = H - 78
        _rrect(d, (16, y0, 16 + max(cw_, 260), H - 16), 12, (24, 28, 34, 225))
        k = f"STEP {ov.step_idx + 1} OF {ov.n_steps}" + (f"   ·   {ov.speed_note}" if ov.speed_note else "")
        d.text((36, y0 + 8), k, font=f_k, fill=(244, 170, 90, 255))
        d.text((36, y0 + 28), cap, font=f_c, fill=(245, 247, 250, 255))
    if ov.footer:
        f_f = font(12)
        fw = d.textlength(ov.footer, font=f_f)
        d.text((W - fw - 16, H - 22), ov.footer, font=f_f, fill=(60, 66, 74, 200))
    img = Image.alpha_composite(img, layer)
    if ov.chart is not None:
        img.alpha_composite(ov.chart, dest=tuple(int(v) for v in ov.chart_pos))
    return img.convert("RGB")


# --------------------------------------------------------------------------- movie
class Movie:
    def __init__(self, name: str, fps: int = FPS, frames_root: Path | None = None):
        self.name = name
        self.fps = fps
        root = frames_root or Path(os.environ.get("FRAMES_DIR", "/tmp/powder-test-frames"))
        self.dir = root / name
        if self.dir.exists():
            shutil.rmtree(self.dir)
        self.dir.mkdir(parents=True)
        self.n = 0

    def add(self, img: Image.Image):
        img.save(self.dir / f"f{self.n:05d}.png", compress_level=1)
        self.n += 1

    def encode(self, gif_width=640, gif_fps=12, gif_colors=160):
        OUT.mkdir(parents=True, exist_ok=True)
        ff = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
        if ff is None:
            import imageio_ffmpeg
            ff = imageio_ffmpeg.get_ffmpeg_exe()
        src = ["-framerate", str(self.fps), "-i", str(self.dir / "f%05d.png")]
        mp4 = OUT / f"{self.name}.mp4"
        gif = OUT / f"{self.name}.gif"
        poster = OUT / f"{self.name}_poster.png"
        subprocess.run([ff, "-y", "-loglevel", "error", *src, "-c:v", "libx264", "-preset", "slow", "-crf", "23",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4)], check=True)
        # GitHub's image proxy will not show GIFs over 5 MiB, so step the frame rate down until it fits
        while True:
            vf = (f"fps={gif_fps},scale={gif_width}:-1:flags=lanczos,split[a][b];"
                  f"[a]palettegen=max_colors={gif_colors}:stats_mode=full[p];"
                  f"[b][p]paletteuse=dither=bayer:bayer_scale=5")
            subprocess.run([ff, "-y", "-loglevel", "error", *src, "-vf", vf, "-loop", "0", str(gif)], check=True)
            if gif.stat().st_size <= GIF_MAX or gif_fps <= 6:
                break
            gif_fps -= 1
        print(self.name, "gif fps", gif_fps, flush=True)
        last = sorted(self.dir.glob("f*.png"))[-1]
        Image.open(last).save(poster, optimize=True)
        sizes = {p.name: f"{p.stat().st_size / 1e6:.2f} MB" for p in (mp4, gif, poster)}
        print(self.name, self.n, "frames", sizes, flush=True)


def frame_range(duration, fps=FPS):
    if os.environ.get("PREVIEW"):
        # PREVIEW="t1,t2,..." renders only those times (seconds), for quick looks
        return [float(x) for x in os.environ["PREVIEW"].split(",")]
    n = int(round(duration * fps))
    return [i / fps for i in range(n)]


def run(scene_fn, name, duration, **encode_kw):
    """Render every frame of scene_fn(t) -> PIL image and encode; PREVIEW renders stills only.

    encode_kw go to Movie.encode (gif_width, gif_fps, gif_colors) to keep GIFs small."""
    times = frame_range(duration)
    if os.environ.get("PREVIEW"):
        outdir = Path(os.environ.get("PREVIEW_DIR", "/tmp/preview"))
        outdir.mkdir(parents=True, exist_ok=True)
        for t in times:
            scene_fn(t).save(outdir / f"{name}_{t:06.2f}.png")
            print("preview", name, t, flush=True)
        return
    mv = Movie(name)
    for i, t in enumerate(times):
        mv.add(scene_fn(t))
        if i % 48 == 0:
            print(name, f"{i}/{len(times)}", flush=True)
    mv.encode(**encode_kw)


if __name__ == "__main__":
    print("helpers only", file=sys.stderr)


# --------------------------------------------------------------------------- shared apparatus pieces
def funnel_geom(z_o, r_o, r_top=29.0, l_orifice=3.2, half_angle=30.0, wall=2.5, lip_h=6.0, lip_w=3.5):
    """Flow-meter funnel (Hall/Carney style): 60-degree cone, short cylindrical orifice.

    Returns (closed (r, z) profile, dict of inner geometry)."""
    k = math.tan(math.radians(half_angle))
    z_ot = z_o + l_orifice
    z_ct = z_ot + (r_top - r_o) / k
    stem = r_o + 3.2
    off = wall / math.cos(math.radians(half_angle))
    z_join = z_ot + max(0.0, (stem - r_o - off) / k)
    r_out_top = r_o + off + k * (z_ct - 1.0 - z_ot)
    prof = [(r_o, z_o), (r_o, z_ot), (r_top, z_ct), (r_top, z_ct + lip_h), (r_top + lip_w, z_ct + lip_h),
            (r_top + lip_w, z_ct - 1.0), (r_out_top, z_ct - 1.0), (stem, z_join), (stem, z_o)]
    z_apex = z_ot - r_o / k
    return prof, dict(z_o=z_o, z_ot=z_ot, z_ct=z_ct, r_o=r_o, r_top=r_top, k=k, z_apex=z_apex,
                      lip_top=z_ct + lip_h, r_lip=r_top + lip_w)


def funnel_level(V, g):
    """Free-surface height in the funnel holding volume V (mm^3)."""
    V_or = math.pi * g["r_o"] ** 2 * (g["z_ot"] - g["z_o"])
    if V <= V_or:
        return g["z_o"] + V / (math.pi * g["r_o"] ** 2)
    c = (V - V_or) * 3.0 / (math.pi * g["k"] ** 2) + (g["z_ot"] - g["z_apex"]) ** 3
    return g["z_apex"] + c ** (1.0 / 3.0)


def funnel_fill(V, g, dip=0.0, a0=0.0, a1=360.0, n=18):
    """Closed lathe solid of powder in a funnel (with an optional central crater depth)."""
    if V <= 1e-6:
        return None
    h = funnel_level(V, g)
    if h <= g["z_ot"]:
        prof = [(0, g["z_o"]), (g["r_o"], g["z_o"]), (g["r_o"], h), (0, h)]
    else:
        rw = g["r_o"] + g["k"] * (h - g["z_ot"])
        d = min(dip, 0.8 * (h - g["z_ot"]))
        surf = [(rw * (1 - i / n), h - d * (i / n)) for i in range(n + 1)]
        prof = [(0, g["z_o"]), (g["r_o"], g["z_o"]), (g["r_o"], g["z_ot"])] + surf
    return lathe(prof, a0=a0, a1=a1)


def heap_solid(R, apex, tan_t, z_base=0.0, a0=0.0, a1=360.0, n=24, r_hole=0.0):
    """Closed lathe solid of a conical heap (slope tan_t) clipped by a cylinder of radius R."""
    if apex <= 1e-3:
        return None
    rr = np.linspace(R, r_hole, n + 1)
    zz = z_base + np.maximum(0.05, apex - rr * tan_t)
    prof = [(r_hole, z_base), (R, z_base)] + list(zip(rr, zz))
    return lathe(prof, a0=a0, a1=a1)


def arrive(t, t0, dur=0.9, offset=(0, 0, 90), rot=0.0, axis=(0, 0, 1), origin=(0, 0, 0)):
    """Assembly motion: (matrix, visible, opacity) easing a part in from `offset` starting at t0."""
    s = ramp(t, t0, t0 + dur)
    M = matrix(translate=np.asarray(offset, float) * (1 - s), rot_deg=rot * (1 - s), axis=axis, origin=origin)
    return M, t >= t0, min(1.0, 0.15 + 0.85 * s / 0.6) if s < 0.6 else 1.0
