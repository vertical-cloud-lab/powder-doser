"""Renders and the animation of the chain-carousel test rig v2 (VTK, offscreen under xvfb-run).

    xvfb-run -a python render.py --stills      # hero views + one image per assembly step + the steps GIF
    xvfb-run -a python render.py --movie       # assembly from scratch, modules onto carriages, carriages onto the chain
                                               #   one index at a time, a lap, a dose at the station, a swap
                                               #   -> renders/chain_carousel_v2.mp4 and .gif
    xvfb-run -a python render.py --quick       # hero iso only

Each unique part is tessellated once (.cache/); every placement is an actor whose matrix is updated per frame from
layout.placements(state), so the animation shows the real chain kinematics (polygonal action included) and the
real station linkage.
"""
from __future__ import annotations

import argparse
import hashlib
import math
from collections import Counter
from pathlib import Path

import numpy as np
import vtk
import vtk.util.numpy_support  # noqa: F401
from PIL import Image, ImageDraw, ImageFont

import layout as L
from params import (CHAIN_L, DOCK_EXT, HOOK_SLIDE, MODULE_LINKS, N_LINKS, N_MODULES, RUN_DIRECTION, SCREW_OUT, TILT_DOSE_WORLD)

SEEK_MM, SEEK_REV_S = 3.0, 0.25          # docking seek (gear-mesh study): pinion turning through the last 3 mm, magnet on
MAG_GAP_DESIGN = 0.15                    # mm, dock magnet face under the steel tab when docked
MAG_F_DESIGN = 20.0 / (1 + MAG_GAP_DESIGN / 0.4) ** 2   # 10.6 N: the gear-mesh study's law for the P20/15 on a 2 mm tab
CENTRE_DIST = 32.25                      # pinion to 44T gear when docked (params.NEMA11_Z)

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache"
OUT = HERE / "renders"
FINE = ("chain", "sprocket", "m3", "insert", "magnet", "nut", "eclip", "clevis_pin", "stub_pin", "loc_pin", "pinion", "hall")


def polydata(key: str) -> vtk.vtkPolyData:
    CACHE.mkdir(exist_ok=True)
    s = L.shape(key)
    bb = s.BoundingBox()
    sig = f"{s.Volume():.3f}|{len(s.Faces())}|{bb.xmin:.3f}|{bb.ymin:.3f}|{bb.zmin:.3f}|{bb.xmax:.3f}|{bb.ymax:.3f}|{bb.zmax:.3f}"
    f = CACHE / f"{key}-{hashlib.sha1(sig.encode()).hexdigest()[:10]}.stl"
    if not f.exists():
        import cadquery as cq
        tol = 0.05 if key.startswith(FINE) else 0.2
        cq.exporters.export(cq.Workplane("XY").add(s), str(f), tolerance=tol, angularTolerance=0.2)
    r = vtk.vtkSTLReader()
    r.SetFileName(str(f))
    r.Update()
    n = vtk.vtkPolyDataNormals()
    n.SetInputConnection(r.GetOutputPort())
    n.SetFeatureAngle(35)
    n.Update()
    return n.GetOutput()


_PD: dict[str, vtk.vtkPolyData] = {}


def vmat(M: np.ndarray) -> vtk.vtkMatrix4x4:
    vm = vtk.vtkMatrix4x4()
    for i in range(4):
        for j in range(4):
            vm.SetElement(i, j, float(M[i, j]))
    return vm


def keyed(pl: list) -> list:
    """(actor key, placement): names made unique by their running count, stable as long as the order of equal
    names doesn't change (carriage and module names carry their number)."""
    c: Counter = Counter()
    out = []
    for p in pl:
        c[p.name] += 1
        out.append((f"{p.name}#{c[p.name]}", p))
    return out


class View:
    def __init__(self, w=1600, h=1000, bg=(1, 1, 1), samples=8):
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(*bg)
        self.win = vtk.vtkRenderWindow()
        self.win.SetOffScreenRendering(1)
        self.win.AddRenderer(self.ren)
        self.win.SetSize(w, h)
        self.win.SetMultiSamples(samples)
        light = vtk.vtkLight()
        light.SetLightTypeToCameraLight()
        light.SetPosition(0.4, 0.6, 1)
        light.SetIntensity(0.5)
        self.ren.AddLight(light)
        self.actors: dict[str, vtk.vtkActor] = {}

    def show(self, pl, colors=None, offsets=None, hide=(), opacity=None, pitch=0.0):
        W = L.world_matrix(pitch)
        seen = set()
        for k, p in keyed(pl):
            if k in hide or p.name in hide:
                continue
            a = self.actors.get(k)
            if a is None or a.GetMapper().GetInput() is not _PD.get(p.key):
                if a is not None:
                    self.ren.RemoveActor(a)
                if p.key not in _PD:
                    _PD[p.key] = polydata(p.key)
                m = vtk.vtkPolyDataMapper()
                m.SetInputData(_PD[p.key])
                a = vtk.vtkActor()
                a.SetMapper(m)
                pr = a.GetProperty()
                pr.SetAmbient(0.25)
                pr.SetDiffuse(0.75)
                pr.SetSpecular(0.15)
                pr.SetSpecularPower(20)
                self.actors[k] = a
                self.ren.AddActor(a)
            M = W @ p.M
            if offsets and (k in offsets or p.name in offsets):
                M = M.copy()
                M[:3, 3] += np.asarray(offsets.get(k, offsets.get(p.name)), float)
            a.SetUserMatrix(vmat(M))
            col = colors.get(k, colors.get(p.name, p.color)) if colors else p.color
            a.GetProperty().SetColor(*col)
            a.GetProperty().SetOpacity(opacity.get(k, opacity.get(p.name, 1.0)) if opacity else 1.0)
            a.VisibilityOn()
            seen.add(k)
        for k, a in self.actors.items():
            if k not in seen:
                a.VisibilityOff()

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
        self.ren.ResetCameraClippingRange()
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


def caption(img: Image.Image, title: str, sub: str = "", corner: str = "") -> Image.Image:
    d = ImageDraw.Draw(img)
    W = img.width
    s = max(16, W // 62)
    d.rectangle([0, 0, W, int(s * (2.9 if sub else 1.7))], fill=(255, 255, 255))
    d.text((int(s * 0.8), int(s * 0.35)), title, fill=(15, 15, 20), font=font(int(s * 1.05)))
    if sub:
        d.text((int(s * 0.8), int(s * 1.6)), sub, fill=(70, 70, 80), font=font(int(s * 0.8)))
    if corner:
        d.text((W - int(s * 0.8) - d.textlength(corner, font=font(int(s * 0.75))), img.height - int(s * 1.4)), corner,
               fill=(90, 90, 100), font=font(int(s * 0.75)))
    return img


def caption_lines(img: Image.Image, title: str, lines: list[str] = ()) -> Image.Image:
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


def front_open(p: L.Placement) -> bool:
    """Hide the front side plate and everything bolted outside it, to look straight at the front chain loop."""
    return (p.key == "side_plate_front" or (p.M[0, 3] < -30.5 and p.key not in ("ext_x", "foot", "board_panel"))
            or (p.key == "m5x12_bhcs" and p.M[0, 3] < -29.0))


def station_cut(p: L.Placement) -> bool:
    """Station close-ups: hide the -y half of the frame, the carriages away from the station and the front plate."""
    if front_open(p):
        return True
    if p.key in ("ext_post", "ext_x", "corner_bracket", "tnut_m5", "m5x12_bhcs") and p.M[1, 3] < 0:
        return True
    return p.module not in (-1, 0) and p.module >= 0 and abs(p.M[1, 3] - L.STATION_Y) > 50


H = L.HINGE_STATION
HERO = ((160, 0, 390), (-0.9, -1.0, 0.55), 1700)
LOOP = ((120, 0, 510), (-1.0, -0.42, 0.22), 1400)
STATION = ((H[0] + 40, H[1], H[2] - 50), (-0.55, -1.0, 0.25), 620)
STATION_TILT = ((H[0] + 60, H[1], H[2] + 10), (-0.35, -1.0, 0.2), 760)
LOADC = ((150, 120, float(L.load_frame()[2, 3]) - 5.0), (0.35, 1.0, 0.35), 950)
TAB = tuple(L.to_world(L.load_frame(), (0.0, L.CAR_W0, L.A1_HOLE_C)))    # carriage 4's front A-1 tab hole at the loading position
YOKE = ((H[0] + 32, H[1] + 10, H[2] - 60), (-0.8, -1.0, 0.25), 330)


def hidden(pl, fn) -> set:
    return {k for k, p in keyed(pl) if fn(p)} if fn else set()


# ---------------------------------------------------------------- stills
def stills(quick: bool = False) -> None:
    OUT.mkdir(exist_ok=True)
    v = View()
    tf = L.frame_dose_tilt(TILT_DOSE_WORLD)
    views = [("rig_iso", L.State(), HERO, None, "Chain carousel v2: 13 carriages on two #35 chains, module 1 docked at the station")]
    if not quick:
        views += [
            ("rig_loop", L.State(), LOOP, front_open, "Front chain loop (front plate hidden): runs with the bottom run toward -y"),
            ("rig_station", L.State(), STATION, station_cut, "Station docked: P16 U-yoke on stub pins at the carriage's COM height, magnet, locating pins"),
            ("rig_tilt30", L.State(tilt=tf), STATION_TILT, station_cut, f"Dosing at {TILT_DOSE_WORLD:.0f} deg: module and electronics carriage tilt together"),
            ("rig_tilt90", L.State(tilt=90.0), ((H[0] + 60, H[1], H[2] + 80), (-0.35, -1.0, 0.2), 950), station_cut,
             "Module 1 at 90 deg (cleaning and access; the P16-150 reaches it with 65 mm of stroke to spare)"),
            ("rig_retracted", L.State(ext=0.0), STATION, station_cut, "Station retracted: the electronics carriage waits 20 mm under the passing carriages"),
            ("rig_yoke", L.State(), YOKE, station_cut, "U-yoke: 2 mm steel arms outside the carriage, stub pins, stop blocks, tongue in the fork"),
            ("rig_load", L.State(out_carriage=3, screws_out=SCREW_OUT, out_slide=HOOK_SLIDE, out_lift=150.0), LOADC, None,
             "Swap at the loading position: two screws out, slide 10 mm, the carriage and its module come out sideways"),
            ("rig_hook", L.State(), (TAB, (-0.6, 1.0, -0.5), 120), front_open,
             "Carriage on an A-1 tab: M3 x 12 from outside, through the tab into a locknut in the printed hook"),
            ("rig_back_iso", L.State(), ((230, 0, 420), (1.0, 0.75, 0.45), 1800), None, "Back: the NEMA 34 inside the frame drives the bottom +y shaft through a #35 drive chain"),
            ("rig_corner", L.State(shift=-4.0), ((70, 80, 380), (-1.0, 0.28, 0.1), 520), front_open, "Bottom +y corner, mid-index"),
        ]
    for name, st, cam, hide_fn, title in views:
        pl = L.placements(st)
        v.show(pl, hide=hidden(pl, hide_fn))
        v.camera(*cam)
        caption(v.image(), title).save(OUT / f"{name}.png")
        print("  wrote", name, flush=True)
    if quick:
        return
    step_images(v)


def step_images(v: View) -> None:
    import bom
    items = bom.step_lines()
    STEP = OUT / "steps"
    STEP.mkdir(exist_ok=True)
    pl = L.placements(L.State(ext=0.0))
    cams = {1: HERO, 2: HERO, 3: HERO, 4: ((150, 0, 470), (-0.9, -1.0, 0.45), 1700), 5: LOOP, 6: ((330, 50, 300), (1.0, 0.85, 0.3), 950),
            7: LOOP, 8: ((H[0] + 50, H[1], H[2] - 90), (-0.6, -1.0, 0.25), 760), 9: LOOP, 10: LOOP,
            11: ((450, 150, 200), (0.45, 1.0, 0.8), 1900)}
    frames = []
    for s in range(1, 12):
        cur = [p for p in pl if p.step <= s]
        hide = hidden(cur, (lambda p: p.step < s and front_open(p))) if s in (5, 7, 9, 10) else set()
        colors = {k: tuple(0.55 + 0.45 * c for c in p.color) for k, p in keyed(cur) if p.step < s}
        offs = {k: np.asarray(p.explode, float) for k, p in keyed(cur) if p.step == s}
        v.show(cur, colors=colors, offsets=offs, hide=hide)
        v.camera(*cams[s])
        img = caption_lines(v.image(), f"Step {s}. {L.STEPS[s]}", items.get(s, [])[:14])
        img.save(STEP / f"step_{s:02d}.png")
        frames.append(img)
        print("  step", s, flush=True)
    small = [f.convert("P", palette=Image.ADAPTIVE, colors=128).resize((960, int(960 * f.height / f.width))) for f in frames]
    small[0].save(OUT / "assembly_steps.gif", save_all=True, append_images=small[1:], duration=2200, loop=0, optimize=True)


# ---------------------------------------------------------------- movie
def ease(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def scurve(t: float, T: float) -> float:
    """Jerk-limited (7th-order smoothstep) fraction of a move at time t of T."""
    x = min(max(t / T, 0.0), 1.0)
    return x ** 4 * (35 - 84 * x + 70 * x ** 2 - 20 * x ** 3)


def cam_lerp(a, b, t):
    t = ease(t)
    return (tuple(np.add(np.multiply(a[0], 1 - t), np.multiply(b[0], t))), tuple(np.add(np.multiply(a[1], 1 - t), np.multiply(b[1], t))),
            a[2] * (1 - t) + b[2] * t)


class Movie:
    """Streams every frame into the MP4 as it is made (nothing full-size is kept: 2000 frames would hold 5.5 GB) and keeps
    only the GIF's frames, every GIF_EVERY-th one, already shrunk to 560 x 315 and palettized (keeps the GIF under 10 MB)."""
    GIF_EVERY = 3

    def __init__(self, mp4: Path, w=1280, h=720, fps=15):
        import os
        import imageio.v2 as iio
        # MOVIE_FPS / MOVIE_SCALE: a cheaper render of the same sequence (the vendor STEPs have threads and knurls, so a
        # frame costs several times what the stand-ins did); the GIF keeps about 5 frames per second
        fps = int(os.environ.get("MOVIE_FPS", fps))
        sc = float(os.environ.get("MOVIE_SCALE", 1.0))
        w, h = int(w * sc) // 8 * 8, int(h * sc) // 8 * 8
        self.GIF_EVERY = max(1, round(fps / 5))
        self.v = View(w, h, samples=4)             # 4x MSAA: half the software-rendering time of the stills' 8x
        self.fps = fps
        self.writer = iio.get_writer(mp4, fps=fps, codec="libx264", quality=7, macro_block_size=8, ffmpeg_params=["-pix_fmt", "yuv420p"])
        self.n = 0
        self.last: Image.Image | None = None
        self.gif: list[Image.Image] = []

    def _emit(self, img: Image.Image) -> None:
        self.writer.append_data(np.asarray(img))
        if self.n % self.GIF_EVERY == 0:
            self.gif.append(img.resize((560, 315), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE, colors=80))
        self.n += 1
        self.last = img

    def frame(self, pl, title, sub="", colors=None, offsets=None, cam=HERO, hide_fn=None, hide=()):
        hs = set(hide) | hidden(pl, hide_fn)
        self.v.show(pl, colors=colors, offsets=offsets, hide=hs)
        self.v.camera(*cam)
        self._emit(caption(self.v.image(), title, sub, "chain carousel v2, #128"))

    def hold(self, n):
        if self.last is not None:
            for _ in range(n):
                self._emit(self.last)

    def close(self) -> None:
        self.writer.close()


def movie(fast: bool = False) -> None:
    OUT.mkdir(exist_ok=True)
    mp4 = OUT / "chain_carousel_v2.mp4"
    mv = Movie(mp4)
    fps = mv.fps
    sec = (lambda s: max(2, int(s * fps * (0.5 if fast else 1.0))))
    dirn = RUN_DIRECTION
    none = ()

    # 1. assembly from scratch: frame, plates, bearings, shafts, drive, chains, station (steps 1-8)
    pl_all = L.placements(L.State(carriages=none, modules=none, ext=0.0))
    for s in range(1, 9):
        n = sec(1.3 if s not in (7, 8) else 2.0)
        cam = HERO if s != 8 else cam_lerp(HERO, STATION, 0.6)
        for i in range(n):
            t = ease(i / (n - 1))
            cur = [p for p in pl_all if p.step <= s]
            offs = {k: np.asarray(p.explode, float) * 3.0 * (1 - t) for k, p in keyed(cur) if p.step == s}
            cols = {k: (0.75, 0.75, 0.78) for k, p in keyed(cur) if p.step < s}
            title, _, sub = L.STEPS[s].partition(": ")
            mv.frame(cur, f"Assembly {s}/11: {title}", sub, colors=cols, offsets=offs, cam=cam)
        mv.hold(sec(0.4))

    # 2. a module on the bench: the auger into Sam's plate (the carrier) and the steel tab, away from the carriage; then the
    #    plate onto the carriage between its hinge lugs, and the two hinge pins
    k0 = 3                                                     # carriage at the loading position at home
    bench = dict(carriages=(k0,), modules=(k0,), ext=0.0, out_carriage=k0, out_slide=HOOK_SLIDE, out_lift=170.0, screws_out=SCREW_OUT)
    pl_b = L.placements(L.State(**bench))
    Cb = next(p.M for p in pl_b if p.key == "carriage" and p.module == k0)
    u_dir, w_dir = Cb[:3, 0], Cb[:3, 1]
    away = w_dir * 110.0                                       # the module is put together 110 mm off the carriage's inner face
    module_keys = ("sam_mounting_plate", "armature_tab", "m3x6_fhcs", "insert_m3", "auger", "auger_cap")

    def pins_out(p, t):                                        # hinge pins and e-clips 40 mm out along their own axis
        su = 1.0 if float(u_dir @ (p.M[:3, 3] - Cb[:3, 3])) > 0 else -1.0
        return su * u_dir * 40.0 * (1 - t)

    beats = [("Module: slide the lab auger into Sam's mounting plate (the carrier)", "threaded-storage auger and cap (PR #170); Sam's Oct 13 plate",
              lambda p, t: (away + (np.array([-170.0 * (1 - t), 0, 0]) if p.key in ("auger", "auger_cap") else 0.0)) if p.key in module_keys
              else pins_out(p, 0.0)),
             ("Module: steel armature tab under the plate's back strip, two M3 flat heads", "the dock magnet pulls on it",
              lambda p, t: (away - (w_dir * 30.0 * (1 - t) if p.key in ("armature_tab", "m3x6_fhcs") else 0.0)) if p.key in module_keys
              else pins_out(p, 0.0)),
             ("Module: the plate goes onto a carriage, its hinge knuckles between the carriage's lugs", "the carriage is the module's mount on the chain",
              lambda p, t: away * (1 - t) if p.key in module_keys else pins_out(p, 0.0)),
             ("Module: two 5 mm clevis pins through the lugs into Sam's knuckles, e-clips on", "the plate's free end snaps under the carriage's two hooks",
              lambda p, t: pins_out(p, t) if p.key in ("clevis_pin", "eclip") else None)]
    for title, sub, off_fn in beats:
        n = sec(1.6)
        for i in range(n):
            t = ease(i / (n - 1))
            pl = L.placements(L.State(**bench))
            offs = {}
            for k, p in keyed(pl):
                if p.module == k0 and (p.key in module_keys or p.key in ("clevis_pin", "eclip")):
                    o = off_fn(p, t)
                    if o is not None:
                        offs[k] = np.asarray(o, float)
            mv.frame(pl, title, sub, offsets=offs, cam=LOADC)
        mv.hold(sec(0.3))

    # 3. carriages onto the chain at the loading position, one index at a time, the way the machine runs
    loaded: list[int] = []
    shift = 0.0
    for j in range(N_MODULES):
        k = (k0 + j) % N_MODULES
        slow = j < 2
        cam = LOADC if slow else cam_lerp(LOADC, HERO, 0.55)
        n_in = sec(1.4 if slow else 0.45)
        for i in range(n_in):                               # in sideways, 10 mm off position
            f = 1.0 - ease(i / (n_in - 1))
            st = L.State(shift=shift, carriages=tuple(loaded + [k]), modules=tuple(loaded + [k]), ext=0.0, station=True,
                         out_carriage=k, out_slide=HOOK_SLIDE, out_lift=170.0 * f, screws_out=SCREW_OUT)
            mv.frame(L.placements(st), f"Carriage {j + 1} of 13 onto the chain at the loading position",
                     "in sideways beside the two A-1 tabs", cam=cam)
        n_s = sec(0.8 if slow else 0.3)
        for i in range(n_s):                                # slide onto the tabs, screws in
            t = ease(i / (n_s - 1))
            st = L.State(shift=shift, carriages=tuple(loaded + [k]), modules=tuple(loaded + [k]), ext=0.0,
                         out_carriage=k, out_slide=HOOK_SLIDE * (1 - min(1, 2 * t)), out_lift=0.0, screws_out=SCREW_OUT * (1 - max(0, 2 * t - 1)))
            mv.frame(L.placements(st), f"Carriage {j + 1} of 13 onto the chain at the loading position",
                     "slide 10 mm so the hooks take the tabs, then two M3 x 12 into the captive locknuts", cam=cam)
        loaded.append(k)
        if j == N_MODULES - 1:
            break
        n_i = sec(1.2 if slow else 0.45)
        for i in range(n_i):
            s = shift + dirn * MODULE_LINKS * scurve(i, n_i - 1)
            mv.frame(L.placements(L.State(shift=s, carriages=tuple(loaded), modules=tuple(loaded), ext=0.0)),
                     "Index one module: 8 links = 1000 motor steps", "bottom run toward -y (auger-leakage study)", cam=cam)
        shift += dirn * MODULE_LINKS
    allm = tuple(range(N_MODULES))

    # 4. one more index puts carriage 1 at the station; then a full lap the way the machine runs
    n_i = sec(0.8)
    for i in range(n_i):
        s = shift + dirn * MODULE_LINKS * scurve(i, n_i - 1)
        mv.frame(L.placements(L.State(shift=s, ext=0.0)), "Index: carriage 1 to the station", "", cam=cam_lerp(LOADC, HERO, 0.55))
    shift += dirn * MODULE_LINKS
    n_lap = sec(6.0)
    for i in range(n_lap):
        s = shift + dirn * N_LINKS * scurve(i, n_lap - 1)
        mv.frame(L.placements(L.State(shift=s, ext=0.0)), "A full lap: each module rolls once about its own axis",
                 "this way round the roll pulls powder back from the outlet", cam=cam_lerp(HERO, LOOP, i / (n_lap - 1)), hide_fn=front_open)
    shift = 0.0

    # 5. dose at the station
    tf = L.frame_dose_tilt(TILT_DOSE_WORLD)
    for i in range(sec(1.2)):
        mv.frame(L.placements(L.State(ext=0.0)), "Station: carriage 1 at the hold-downs", "", cam=cam_lerp(LOOP, STATION, i / (sec(1.2) - 1)),
                 hide_fn=station_cut)
    for i in range(sec(1.4)):
        e = (DOCK_EXT - SEEK_MM) * ease(i / (sec(1.4) - 1))
        mv.frame(L.placements(L.State(ext=e)), "Actuonix P16-P lifts the electronics carriage through the carriage window",
                 f"approach {e:4.1f} mm, the yoke's tongue in the fork", cam=STATION, hide_fn=station_cut)
    n_s = sec(1.6)
    for i in range(n_s):
        f = i / (n_s - 1)
        e = DOCK_EXT - SEEK_MM * (1 - f)
        seek = 2 * math.pi * SEEK_REV_S * 1.6 * f * 20.0 / 44.0      # auger angle once the pinion's teeth find the gaps
        mv.frame(L.placements(L.State(ext=e, magnet_on=True, spin=seek)),
                 f"Docking seek: magnet on, the pinion turns at {SEEK_REV_S} rev/s through the last {SEEK_MM:.0f} mm",
                 "its teeth find the 44T gear's gaps; the locating pins enter the plate", cam=STATION, hide_fn=station_cut)
    seek_end = 2 * math.pi * SEEK_REV_S * 1.6 * 20.0 / 44.0
    for i in range(sec(0.8)):
        mv.frame(L.placements(L.State(magnet_on=True, spin=seek_end)),
                 f"Docked: the magnet pulls the steel tab with about {MAG_F_DESIGN:.1f} N at the {MAG_GAP_DESIGN} mm design gap",
                 f"the rim sets the {CENTRE_DIST} mm centre distance", cam=STATION, hide_fn=station_cut)
    for i in range(sec(2.2)):
        a = tf * ease(i / (sec(2.2) - 1))
        mv.frame(L.placements(L.State(tilt=a, magnet_on=True, spin=seek_end)), "Tilt: the plate leaves the snap hooks, module and carriage turn together",
                 f"tilt {a:4.1f} deg", cam=cam_lerp(STATION, STATION_TILT, i / (sec(2.2) - 1)), hide_fn=station_cut)
    n_d = sec(2.4)
    for i in range(n_d):
        spin = seek_end + 2 * math.pi * 1.0 * i / (n_d - 1)
        tap = 2.0 if (i // max(1, fps // 4)) % 2 == 0 and i > n_d * 0.6 else 0.0
        mv.frame(L.placements(L.State(tilt=tf, magnet_on=True, spin=spin, tap=tap)),
                 f"Dosing at {TILT_DOSE_WORLD:.0f} deg: NEMA 11 turns the auger through the steel 20T pinion and the 44T gear",
                 f"auger {(spin - seek_end) / (2 * math.pi):4.2f} rev", cam=STATION_TILT, hide_fn=station_cut)
    mv.hold(sec(0.5))
    for i in range(sec(1.6)):
        a = tf * (1 - ease(i / (sec(1.6) - 1)))
        mv.frame(L.placements(L.State(tilt=a, magnet_on=True, spin=seek_end + 2 * math.pi)), "Hold 0.5 s, then tilt back to level", f"tilt {a:4.1f} deg",
                 cam=cam_lerp(STATION_TILT, STATION, i / (sec(1.6) - 1)), hide_fn=station_cut)
    n_r = sec(1.6)
    for i in range(n_r):
        spin = seek_end + 2 * math.pi * (1 - i / (n_r - 1))
        mv.frame(L.placements(L.State(magnet_on=True, spin=spin)), "At rest: reverse the auger one turn",
                 "pulls powder back from the exit (auger-leakage study); never while tilted", cam=STATION, hide_fn=station_cut)
    for i in range(sec(1.2)):
        e = DOCK_EXT - DOCK_EXT * ease(i / (sec(1.2) - 1))
        mv.frame(L.placements(L.State(ext=e, magnet_on=e > DOCK_EXT - 2.0, spin=seek_end)), "Undock: press the plate into the snap hooks, magnet off, retract",
                 "", cam=STATION, hide_fn=station_cut)

    # 6. swap the module at the loading position
    k_sw = k0
    for i in range(sec(1.2)):
        mv.frame(L.placements(L.State(ext=0.0)), "Swap a module at the loading position", "", cam=cam_lerp(STATION, LOADC, i / (sec(1.2) - 1)))
    for title, sub, fn in (("Swap: two M3 screws out", "", lambda t: dict(screws_out=SCREW_OUT * t)),
                           ("Swap: slide the carriage 10 mm so its hooks clear the tabs", "", lambda t: dict(screws_out=SCREW_OUT, out_slide=HOOK_SLIDE * t)),
                           ("Swap: carriage and module come out sideways", "the module stays on its own carriage",
                            lambda t: dict(screws_out=SCREW_OUT, out_slide=HOOK_SLIDE, out_lift=170.0 * t))):
        n = sec(1.1)
        for i in range(n):
            t = ease(i / (n - 1))
            mv.frame(L.placements(L.State(ext=0.0, out_carriage=k_sw, **fn(t))), title, sub, cam=LOADC)
    new_col = None
    for title, fn in (("Swap: a different powder's carriage goes in", lambda t: dict(screws_out=SCREW_OUT, out_slide=HOOK_SLIDE, out_lift=170.0 * (1 - t))),
                      ("Swap: slide onto the tabs, screws in. Done", lambda t: dict(screws_out=SCREW_OUT * (1 - t), out_slide=HOOK_SLIDE * (1 - t)))):
        n = sec(1.1)
        for i in range(n):
            t = ease(i / (n - 1))
            pl = L.placements(L.State(ext=0.0, out_carriage=k_sw, **fn(t)))
            new_col = {k: (0.1, 0.65, 0.35) for k, p in keyed(pl) if p.module == k_sw and p.key in ("sam_mounting_plate", "auger_cap", "carriage")}
            mv.frame(pl, title, "", colors=new_col, cam=LOADC)
    mv.hold(sec(1.5))

    mv.close()
    gif = OUT / "chain_carousel_v2.gif"
    mv.gif[0].save(gif, save_all=True, append_images=mv.gif[1:], duration=int(1000 * Movie.GIF_EVERY / fps), loop=0, optimize=True)
    print(f"  {mv.n} frames ({mv.n / fps:.1f} s) -> {mp4.name} ({mp4.stat().st_size / 1e6:.1f} MB), {gif.name} ({gif.stat().st_size / 1e6:.1f} MB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--movie", action="store_true")
    ap.add_argument("--fast", action="store_true", help="half-length movie (for checking)")
    a = ap.parse_args()
    if a.movie:
        movie(a.fast)
    else:
        stills(quick=a.quick)


if __name__ == "__main__":
    main()
