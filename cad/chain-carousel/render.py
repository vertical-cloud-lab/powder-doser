"""Renders of the chain-carousel test rig (VTK, offscreen under xvfb-run).

    xvfb-run -a python render.py            # hero views + one image per assembly step + GIF
    xvfb-run -a python render.py --quick    # hero iso only

Each unique part is tessellated once (cache/), every placement is an actor
with its own transform. Step images show everything built so far in grey
and the step's new parts in colour, lifted along their insertion offsets.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import vtk
from PIL import Image, ImageDraw, ImageFont

import layout as L

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache"
OUT = HERE / "renders"


def polydata(key: str) -> vtk.vtkPolyData:
    import hashlib
    CACHE.mkdir(exist_ok=True)
    s = L.shape(key)
    bb = s.BoundingBox()
    sig = f"{s.Volume():.3f}|{len(s.Faces())}|{bb.xmin:.3f}|{bb.ymin:.3f}|{bb.zmin:.3f}|{bb.xmax:.3f}|{bb.ymax:.3f}|{bb.zmax:.3f}"
    f = CACHE / f"{key}-{hashlib.sha1(sig.encode()).hexdigest()[:10]}.stl"
    if not f.exists():
        import cadquery as cq
        tol = 0.05 if key.startswith(("chain", "sprocket", "m3", "insert", "magnet", "a3144")) else 0.2
        cq.exporters.export(cq.Workplane("XY").add(L.shape(key)), str(f), tolerance=tol, angularTolerance=0.2)
    r = vtk.vtkSTLReader()
    r.SetFileName(str(f))
    r.Update()
    n = vtk.vtkPolyDataNormals()
    n.SetInputConnection(r.GetOutputPort())
    n.SetFeatureAngle(35)
    n.Update()
    return n.GetOutput()


_PD: dict[str, vtk.vtkPolyData] = {}


def actor(p: L.Placement, color, offset=(0, 0, 0), opacity=1.0) -> vtk.vtkActor:
    if p.key not in _PD:
        _PD[p.key] = polydata(p.key)
    m = vtk.vtkPolyDataMapper()
    m.SetInputData(_PD[p.key])
    a = vtk.vtkActor()
    a.SetMapper(m)
    M = p.M.copy()
    M[:3, 3] += np.asarray(offset, float)
    vm = vtk.vtkMatrix4x4()
    for i in range(4):
        for j in range(4):
            vm.SetElement(i, j, float(M[i, j]))
    a.SetUserMatrix(vm)
    pr = a.GetProperty()
    pr.SetColor(*color)
    pr.SetOpacity(opacity)
    pr.SetAmbient(0.25)
    pr.SetDiffuse(0.75)
    pr.SetSpecular(0.15)
    pr.SetSpecularPower(20)
    return a


class View:
    def __init__(self, w=1600, h=1100, bg=(1, 1, 1)):
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(*bg)
        self.win = vtk.vtkRenderWindow()
        self.win.SetOffScreenRendering(1)
        self.win.AddRenderer(self.ren)
        self.win.SetSize(w, h)
        self.win.SetMultiSamples(8)
        light = vtk.vtkLight()
        light.SetLightTypeToCameraLight()
        light.SetPosition(0.4, 0.6, 1)
        light.SetIntensity(0.5)
        self.ren.AddLight(light)

    def clear(self):
        self.ren.RemoveAllViewProps()

    def camera(self, focal, direction, dist, up=(0, 0, 1), view_angle=30.0):
        cam = self.ren.GetActiveCamera()
        d = np.asarray(direction, float)
        d /= np.linalg.norm(d)
        cam.SetFocalPoint(*focal)
        cam.SetPosition(*(np.asarray(focal) + d * dist))
        cam.SetViewUp(*up)
        cam.SetViewAngle(view_angle)
        self.ren.ResetCameraClippingRange()

    def image(self) -> Image.Image:
        self.win.Render()
        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(self.win)
        w2i.SetInputBufferTypeToRGB()
        w2i.ReadFrontBufferOff()
        w2i.Update()
        img = w2i.GetOutput()
        w, h, _ = img.GetDimensions()
        arr = vtk.util.numpy_support.vtk_to_numpy(img.GetPointData().GetScalars()).reshape(h, w, 3)
        return Image.fromarray(np.flipud(arr))


def font(size):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def caption(img: Image.Image, title: str, lines: list[str] = ()) -> Image.Image:
    """Title and the step's BoM lines on a white band above the render."""
    band = 70 + 30 * len(lines) + 12
    out = Image.new("RGB", (img.width, img.height + band), (255, 255, 255))
    out.paste(img, (0, band))
    d = ImageDraw.Draw(out)
    d.text((28, 18), title, fill=(20, 20, 20), font=font(34))
    y = 66
    for ln in lines:
        d.text((30, y), ln, fill=(70, 70, 70), font=font(22))
        y += 30
    d.line((0, band - 1, img.width, band - 1), fill=(210, 210, 210), width=2)
    return out


HERO = dict(focal=(60, -60, -90), direction=(0.55, -1.0, 0.75), dist=2050)
CAMS = {
    "iso": HERO,
    "top": dict(focal=(0, 0, 0), direction=(0, -0.0001, 1), dist=2500, up=(0, 1, 0)),
    "front": dict(focal=(0, 0, -120), direction=(0, -1, 0.0001), dist=2600),
    "station": dict(focal=(-7, -230, 20), direction=(0.9, -1.0, 0.9), dist=820),
    "drive": dict(focal=(183, 0, -100), direction=(1.0, -1.3, -0.35), dist=950),
    "idler": dict(focal=(-190, 0, 0), direction=(-0.6, -1.0, 1.0), dist=520),
    "chain_detail": dict(focal=(150, -40, 8), direction=(0.3, -1.0, 1.0), dist=260),
}


def hero_views(view: View, pl, tag=""):
    view.clear()
    for p in pl:
        view.ren.AddActor(actor(p, p.color))
    out = {}
    for name, cam in CAMS.items():
        view.camera(**cam)
        img = view.image()
        f = OUT / f"rig_{name}{tag}.png"
        img.save(f)
        out[name] = f
    return out


def step_images(view: View, pl, bom_items: dict[int, list[str]]):
    frames = []
    for s, title in L.STEPS.items():
        view.clear()
        under_deck = s in (5, 7)                    # new parts go in from below the deck
        for p in pl:
            if p.step < s:
                faded = tuple(0.55 + 0.45 * c for c in p.color)
                op = 0.25 if (under_deck and p.key == "deck") else 1.0
                view.ren.AddActor(actor(p, faded, opacity=op))
            elif p.step == s:
                view.ren.AddActor(actor(p, p.color, offset=p.explode))
        cam = step_camera(s)
        view.camera(**cam)
        img = view.image()
        img = caption(img, f"Step {s}. {title}", bom_items.get(s, [])[:14])
        f = OUT / "steps" / f"step_{s:02d}.png"
        f.parent.mkdir(parents=True, exist_ok=True)
        img.save(f)
        # assembled state of the step too (offsets removed) for the GIF
        frames.append(img)
    return frames


def step_camera(s: int) -> dict:
    if s in (1, 2):
        return dict(focal=(0, 0, -120), direction=(0.55, -1.0, 0.6), dist=2100)
    if s == 3:
        return dict(focal=(183, 0, -160), direction=(1.0, -1.2, 0.35), dist=1100)
    if s == 6:
        return dict(focal=(183, 0, -10), direction=(0.9, -1.0, 0.9), dist=520)
    if s == 5:
        return dict(focal=(-190, 0, -20), direction=(-0.7, -1.0, 0.55), dist=560)
    if s == 7:
        return dict(focal=(-7, -80, -20), direction=(0.5, -1.0, 0.6), dist=520)
    if s in (10, 11):
        return dict(focal=(-7, -200, 30), direction=(0.9, -1.0, 0.9), dist=900)
    if s == 12:
        return dict(focal=(150, -450, -200), direction=(0.6, -1.0, 0.8), dist=1600)
    if s == 8:
        return dict(focal=(0, 0, 0), direction=(0.45, -1.0, 1.0), dist=1050)
    return HERO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    pl = L.placements()
    view = View()
    if a.quick:
        view.clear()
        for p in pl:
            view.ren.AddActor(actor(p, p.color))
        view.camera(**HERO)
        view.image().save(OUT / "rig_iso_quick.png")
        return
    hero_views(view, pl)
    import bom
    items = bom.step_lines()
    frames = step_images(view, pl, items)
    frames[0].save(OUT / "assembly_steps.gif", save_all=True, append_images=frames[1:],
                   duration=[2200] * len(frames), loop=0, optimize=True)


if __name__ == "__main__":
    import vtk.util.numpy_support  # noqa: F401
    main()
