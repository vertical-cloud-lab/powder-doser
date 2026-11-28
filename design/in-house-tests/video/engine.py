"""Small off-screen animation engine for the assembly and SOP videos (pyvista + PIL + ffmpeg).

A Scene holds one VTK actor per component; frames move actors by setting their user matrices, so
meshes are uploaded once. Overlays (title, step caption, inset plot) are drawn with PIL on each
screenshot. Frames stream into an H.264 MP4 through imageio-ffmpeg.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
import pyvista as pv
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "cad"))

pv.OFF_SCREEN = True
W, H = 1280, 720
FPS = 24

_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size, bold=False):
    try:
        return ImageFont.truetype(_FONTB if bold else _FONT, size)
    except OSError:
        return ImageFont.load_default()


def ease(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def T(tx=0.0, ty=0.0, tz=0.0, rx=0.0, ry=0.0, rz=0.0):
    from assemblies import T as _T
    return _T(tx, ty, tz, rx, ry, rz)


def rot_about(axis_point, axis_dir, deg):
    """4x4 rotation by deg about a line through axis_point along axis_dir."""
    import trimesh
    return trimesh.transformations.rotation_matrix(math.radians(deg), axis_dir, axis_point)


class Scene:
    def __init__(self, comps, bg="white", size=(W, H)):
        self.pl = pv.Plotter(off_screen=True, window_size=size)
        self.pl.set_background(bg)
        self.pl.enable_anti_aliasing("ssaa") if hasattr(self.pl, "enable_anti_aliasing") else None
        self.comps = comps
        self.actors = []
        for c in comps:
            if c.opacity <= 0:
                self.actors.append(None)
                continue
            a = self.pl.add_mesh(pv.wrap(c.mesh), color=c.color, opacity=c.opacity, smooth_shading=False,
                                 specular=0.25 if c.kind != "context" else 0.05, specular_power=20)
            a.user_matrix = c.M
            self.actors.append(a)
        self._pts_actor = {}
        self.size = size

    # -- actors ---------------------------------------------------------------------------------
    def pose(self, i, M):
        if self.actors[i] is not None:
            self.actors[i].user_matrix = M

    def show(self, i, flag=True):
        if self.actors[i] is not None:
            self.actors[i].SetVisibility(bool(flag))

    def opacity(self, i, val):
        if self.actors[i] is not None:
            self.actors[i].GetProperty().SetOpacity(val)

    def group(self, name):
        return [i for i, c in enumerate(self.comps) if c.group == name]

    def particles(self, key, pts, color="#d9b98a", size_px=6.0):
        """Point sprites rendered as spheres; one actor per key, updated in place."""
        pts = np.asarray(pts, float).reshape(-1, 3)
        if len(pts) == 0:
            pts = np.array([[0.0, 0.0, -1e4]])
        if key not in self._pts_actor:
            poly = pv.PolyData(pts)
            a = self.pl.add_mesh(poly, color=color, point_size=size_px, render_points_as_spheres=True,
                                 lighting=True, specular=0.3)
            self._pts_actor[key] = (a, poly)
        else:
            a, poly = self._pts_actor[key]
            if len(pts) != poly.n_points:
                new = pv.PolyData(pts)
                poly.copy_from(new)
            else:
                poly.points = pts
            a.GetProperty().SetPointSize(size_px)

    def add_mesh(self, mesh, **kw):
        return self.pl.add_mesh(pv.wrap(mesh), **kw)

    # -- camera ---------------------------------------------------------------------------------
    def camera(self, focus, azim, elev, dist, view_angle=30.0):
        az, el = math.radians(azim - 90), math.radians(elev)
        f = np.array(focus, float)
        pos = f + dist * np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
        cam = self.pl.camera
        cam.position = tuple(pos)
        cam.focal_point = tuple(f)
        cam.up = (0, 0, 1)
        cam.view_angle = view_angle
        self.pl.renderer.ResetCameraClippingRange()

    def grab(self) -> np.ndarray:
        self.pl.render()
        return np.asarray(self.pl.screenshot(return_img=True))

    def close(self):
        self.pl.close()


# ---------------------------------------------------------------------------------------------------
# overlays
# ---------------------------------------------------------------------------------------------------

def overlay(img: np.ndarray, title: str = "", caption: str = "", step: str = "", tag: str = "",
            inset=None) -> np.ndarray:
    im = Image.fromarray(img).convert("RGBA")
    d = ImageDraw.Draw(im, "RGBA")
    w, h = im.size
    if title:
        d.rectangle([0, 0, w, 52], fill=(255, 255, 255, 215))
        d.text((24, 12), title, font=font(26, True), fill=(20, 20, 20, 255))
    if tag:
        tw = d.textlength(tag, font=font(18))
        d.rounded_rectangle([w - tw - 44, 12, w - 20, 42], radius=8, fill=(42, 157, 143, 230))
        d.text((w - tw - 32, 16), tag, font=font(18, True), fill=(255, 255, 255, 255))
    if caption:
        d.rectangle([0, h - 70, w, h], fill=(25, 25, 25, 200))
        x = 24
        if step:
            d.rounded_rectangle([20, h - 56, 20 + 30 + 13 * len(step), h - 16], radius=8, fill=(123, 94, 167, 255))
            d.text((32, h - 52), step, font=font(24, True), fill=(255, 255, 255, 255))
            x = 20 + 30 + 13 * len(step) + 18
        d.text((x, h - 52), caption, font=font(25), fill=(255, 255, 255, 255))
    if inset is not None:
        inset.draw(d)
    return np.asarray(im.convert("RGB"))


class Inset:
    """A small line plot drawn with PIL: x/y data revealed progressively."""

    def __init__(self, box, xlabel, ylabel, xlim, ylim, title="", logx=False, series=None, hlines=None):
        self.box = box          # (x0, y0, x1, y1) in pixels
        self.xlabel, self.ylabel, self.title = xlabel, ylabel, title
        self.xlim, self.ylim, self.logx = xlim, ylim, logx
        self.series = series or []   # list of dict(x=..., y=..., color=..., n=visible count, style)
        self.hlines = hlines or []
        self.note = ""

    def _px(self, x, y):
        x0, y0, x1, y1 = self.box
        if self.logx:
            x = math.log10(max(x, 1e-9))
            lo, hi = math.log10(self.xlim[0]), math.log10(self.xlim[1])
        else:
            lo, hi = self.xlim
        fx = (x - lo) / (hi - lo)
        fy = (y - self.ylim[0]) / (self.ylim[1] - self.ylim[0])
        return x0 + 50 + fx * (x1 - x0 - 62), y1 - 34 - fy * (y1 - y0 - 62)

    def draw(self, d: ImageDraw.ImageDraw):
        x0, y0, x1, y1 = self.box
        d.rounded_rectangle(self.box, radius=10, fill=(255, 255, 255, 235), outline=(160, 160, 160, 255))
        if self.title:
            d.text((x0 + 12, y0 + 6), self.title, font=font(16, True), fill=(30, 30, 30, 255))
        ax0, ay1 = x0 + 50, y1 - 34
        ax1, ay0 = x1 - 12, y0 + 28
        d.line([(ax0, ay0), (ax0, ay1), (ax1, ay1)], fill=(80, 80, 80, 255), width=2)
        d.text((ax0 + (ax1 - ax0) / 2 - 4 * len(self.xlabel), y1 - 26), self.xlabel, font=font(14), fill=(60, 60, 60, 255))
        d.text((x0 + 6, ay0 - 2), self.ylabel, font=font(14), fill=(60, 60, 60, 255))
        for val, lab in ((self.ylim[0], f"{self.ylim[0]:g}"), (self.ylim[1], f"{self.ylim[1]:g}")):
            px, py = self._px(self.xlim[0], val)
            d.text((x0 + 6, py - 8), lab, font=font(12), fill=(90, 90, 90, 255))
        for val in (self.xlim[0], self.xlim[1]):
            px, py = self._px(val, self.ylim[0])
            d.text((px - 8, ay1 + 2), f"{val:g}", font=font(12), fill=(90, 90, 90, 255))
        for yv, col in self.hlines:
            p0, p1 = self._px(self.xlim[0], yv), self._px(self.xlim[1], yv)
            d.line([p0, p1], fill=col, width=1)
        for s in self.series:
            n = int(s.get("n", len(s["x"])))
            pts = [self._px(x, y) for x, y in zip(s["x"][:n], s["y"][:n])]
            if s.get("style", "line") == "line" and len(pts) > 1:
                d.line(pts, fill=s.get("color", (42, 157, 143, 255)), width=3)
            else:
                for p in pts:
                    d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill=s.get("color", (123, 94, 167, 255)))
        if self.note:
            d.text((x0 + 60, y0 + 30), self.note, font=font(15, True), fill=(123, 94, 167, 255))


def title_card(title: str, subtitle: str, lines=(), size=(W, H)) -> np.ndarray:
    im = Image.new("RGB", size, (250, 250, 250))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 18, size[1]], fill=(42, 157, 143))
    d.text((70, 200), title, font=font(54, True), fill=(20, 20, 20))
    d.text((72, 285), subtitle, font=font(28), fill=(70, 70, 70))
    for i, ln in enumerate(lines):
        d.text((72, 360 + 40 * i), ln, font=font(24), fill=(90, 90, 90))
    d.text((72, size[1] - 70), "Concept design, not built. In-house powder tests on the doser (PR #205).",
           font=font(18), fill=(130, 130, 130))
    return np.asarray(im)


class Writer:
    def __init__(self, path, fps=FPS):
        self.w = imageio.get_writer(str(path), fps=fps, codec="libx264", quality=7, macro_block_size=8,
                                    ffmpeg_params=["-pix_fmt", "yuv420p", "-preset", "veryfast"])
        self.n = 0

    def add(self, frame, repeat=1):
        for _ in range(repeat):
            self.w.append_data(frame)
            self.n += 1

    def close(self):
        self.w.close()
