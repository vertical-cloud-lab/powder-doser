"""Renders and animations of the paternoster carousel (VTK, offscreen under xvfb-run).

    xvfb-run -a python render.py --stills      # hero views + one image per assembly step
    xvfb-run -a python render.py --movie       # assembly-from-scratch + loading + indexing + station + swap
                                               #   -> renders/paternoster.mp4 and renders/paternoster.gif
    xvfb-run -a python render.py --quick       # hero iso only

Each unique part is tessellated once (.cache/); every placement is an actor
whose matrix is updated per frame from layout.placements(state), so the
animation shows the real chain kinematics (polygonal action included).
"""
from __future__ import annotations

import argparse
import hashlib
import math
from pathlib import Path

import numpy as np
import vtk
from PIL import Image, ImageDraw, ImageFont
from vtk.util import numpy_support

import kinematics as K
import layout as L
from params import N_MODULES, MODULE_LINKS, TILT_MAX

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache"
OUT = HERE / "renders"
FINE = ("chain", "sprocket", "shoulder", "nut", "thrust", "sleeve", "insert", "thumb", "pinion", "hall")


def polydata(key: str) -> vtk.vtkPolyData:
    CACHE.mkdir(exist_ok=True)
    s = L.shape(key)
    bb = s.BoundingBox()
    sig = f"{s.Volume():.3f}|{len(s.Faces())}|{bb.xmin:.3f}|{bb.ymin:.3f}|{bb.zmin:.3f}|{bb.xmax:.3f}|{bb.ymax:.3f}|{bb.zmax:.3f}"
    f = CACHE / f"{key}-{hashlib.sha1(sig.encode()).hexdigest()[:10]}.stl"
    if not f.exists():
        import cadquery as cq
        tol = 0.05 if key.startswith(FINE) else 0.25
        cq.exporters.export(cq.Workplane("XY").add(s), str(f), tolerance=tol, angularTolerance=0.25)
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


def make_actor(key: str, color, opacity=1.0) -> vtk.vtkActor:
    if key not in _PD:
        _PD[key] = polydata(key)
    m = vtk.vtkPolyDataMapper()
    m.SetInputData(_PD[key])
    a = vtk.vtkActor()
    a.SetMapper(m)
    pr = a.GetProperty()
    pr.SetColor(*color)
    pr.SetOpacity(opacity)
    pr.SetAmbient(0.25)
    pr.SetDiffuse(0.75)
    pr.SetSpecular(0.15)
    pr.SetSpecularPower(20)
    return a


class View:
    def __init__(self, w=1600, h=1000, bg=(1, 1, 1)):
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(*bg)
        self.win = vtk.vtkRenderWindow()
        self.win.SetOffScreenRendering(1)
        self.win.AddRenderer(self.ren)
        self.win.SetSize(w, h)
        self.win.SetMultiSamples(4)
        light = vtk.vtkLight()
        light.SetLightTypeToCameraLight()
        light.SetPosition(0.4, 0.6, 1)
        light.SetIntensity(0.45)
        self.ren.AddLight(light)
        self.actors: dict[str, vtk.vtkActor] = {}

    def camera(self, focal, direction, dist, up=(0, 0, 1), view_angle=30.0):
        cam = self.ren.GetActiveCamera()
        d = np.asarray(direction, float)
        d /= np.linalg.norm(d)
        cam.SetFocalPoint(*focal)
        cam.SetPosition(*(np.asarray(focal) + d * dist))
        cam.SetViewUp(*up)
        cam.SetViewAngle(view_angle)
        self.ren.ResetCameraClippingRange()

    def show(self, pl: list, colors=None, opacity=None, offsets=None, hide=()) -> None:
        """Place every placement (by name); actors not in pl are hidden."""
        seen = set()
        for p in pl:
            if p.name in hide:
                continue
            a = self.actors.get(p.name)
            if a is None:
                a = make_actor(p.key, p.color)
                self.actors[p.name] = a
                self.ren.AddActor(a)
            M = p.M.copy()
            if offsets and p.name in offsets:
                M[:3, 3] += offsets[p.name]
            a.SetUserMatrix(vmat(M))
            a.GetProperty().SetColor(*(colors.get(p.name, p.color) if colors else p.color))
            a.GetProperty().SetOpacity(opacity.get(p.name, 1.0) if opacity else 1.0)
            a.VisibilityOn()
            seen.add(p.name)
        for n, a in self.actors.items():
            if n not in seen:
                a.VisibilityOff()

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
        arr = numpy_support.vtk_to_numpy(img.GetPointData().GetScalars()).reshape(h, w, 3)
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


FOCAL = (160.0, 0.0, 420.0)


def cutaway(pl, keep: set) -> set:
    """Names of the gondolas, modules and pivot parts not in keep (station close-ups)."""
    return {p.name for p in pl if p.module >= 0 and p.module not in keep}
ISO = (-0.5, 1.0, 0.45)


# ---------------------------------------------------------------- stills
def stills(quick: bool = False) -> None:
    OUT.mkdir(exist_ok=True)
    v = View()
    views = [
        ("rig_iso", L.State(), FOCAL, ISO, 1900, "Paternoster carousel, home: 12 gondolas, module 1 at the station"),
    ]
    if not quick:
        views += [
            ("rig_front", L.State(), (160, 0, 470), (-1, 0, 0.02), 1500, "From the front (side plate on): the loop, gondolas upright all the way round"),
            ("rig_loop", L.State(), (160, 0, 470), (-1, 0.0, 0.02), 1500, "Front chain loop (front plate and bearings hidden)"),
            ("rig_station_tilt30", L.State(tilt=30.0), (95, 0, 310), (-0.35, 1.0, 0.12), 640, "Station: module 1 tilted 30 deg (dosing range 20-40 deg, sim/AUGER-SIM.md) by the Actuonix P16-P"),
            ("rig_station_tilt90", L.State(tilt=90.0), (110, 0, 380), (-0.35, 1.0, 0.15), 820, "Station: module 1 at 90 deg, cap end up into the empty middle of the loop"),
            ("rig_station_approach", L.State(ext=0.0), (80, 0, 290), (-0.35, 1.0, 0.08), 560, "Station retracted: the electronics carriage waits below the gondolas' path"),
            ("rig_load", L.State(out_module=3, out_frac=1.0), (180, 160, 520), (0.15, 1.0, 0.35), 720, "Loading position (right side, mid-height): module 4 lifted and slid out"),
            ("rig_pivot", L.State(), (0, 153.1, 534.3), (-0.6, 0.8, 0.45), 120, "Pivot: SA-1 link, M3 x 4 x 10 shoulder screw, PTFE washers, bronze bushing, nylock"),
            ("rig_top_corner", L.State(shift=K.HOME_SHIFT + 6.0), (20, 95, 690), (-0.9, 0.35, 0.3), 420, "Top corner: the gondola passes over the flush idler axle"),
            ("rig_drive", L.State(), (420, 95, 420), (0.7, 0.9, 0.35), 900, "Drive: NEMA 34 straight onto the bottom shaft through an L090 jaw coupling"),
        ]
    for name, st, focal, d, dist, title in views:
        pl = L.placements(st)
        hide = set()
        if name.startswith("rig_station"):
            hide = cutaway(pl, {L.station_module(st)})
        if name == "rig_loop":
            hide = {p.name for p in pl if p.key in ("side_plate_front", "flange_bearing", "idler_axle", "nut_m10", "ext_post", "ext_y", "corner_bracket")
                    and (p.M[0, 3] < 0)}
        v.show(pl, hide=hide)
        v.camera(focal, d, dist)
        img = caption(v.image(), title)
        img.save(OUT / f"{name}.png")
        print("  wrote", name, flush=True)
    if quick:
        return
    # assembly steps: everything so far grey, the step's new parts in colour, lifted along their offsets
    STEP = OUT / "steps"
    STEP.mkdir(exist_ok=True)
    pl = L.placements(L.State(ext=0.0))
    for s in range(1, 12):
        cur = [p for p in pl if p.step <= s]
        colors = {p.name: (0.78, 0.78, 0.8) for p in cur if p.step < s}
        offs = {p.name: np.asarray(p.explode, float) for p in cur if p.step == s}
        v.show(cur, colors=colors, offsets=offs)
        foc = {10: (95, 0, 280), 11: (60, 0, 280)}.get(s, FOCAL)
        dist = {10: 1000, 11: 800}.get(s, 1900)
        v.camera(foc, ISO, dist)
        img = caption(v.image(), f"Step {s}: {L.STEP_TITLES[s]}")
        img.save(STEP / f"step_{s:02d}.png")
        print("  step", s, flush=True)
    frames = [Image.open(STEP / f"step_{s:02d}.png").convert("P", palette=Image.ADAPTIVE, colors=128).resize((960, 600)) for s in range(1, 12)]
    frames[0].save(OUT / "assembly_steps.gif", save_all=True, append_images=frames[1:], duration=1600, loop=0, optimize=True)


# ---------------------------------------------------------------- movie
def ease(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def scurve_shift(t: float, T: float) -> float:
    """Jerk-limited (7th-order smoothstep) fraction of one index at time t of T."""
    x = min(max(t / T, 0.0), 1.0)
    return x ** 4 * (35 - 84 * x + 70 * x ** 2 - 20 * x ** 3)


class Movie:
    def __init__(self, w=1280, h=720, fps=24):
        self.v = View(w, h)
        self.fps = fps
        self.frames: list[Image.Image] = []
        self.cam = (FOCAL, ISO, 1900)

    def frame(self, pl, title, sub="", colors=None, offsets=None, cam=None, hide=()):
        f, d, dist = cam or self.cam
        self.v.show(pl, colors=colors, offsets=offsets, hide=hide)
        self.v.camera(f, d, dist)
        img = caption(self.v.image(), title, sub, "paternoster multi-doser, #128")
        self.frames.append(img)

    def hold(self, n):
        if self.frames:
            self.frames += [self.frames[-1]] * n


def cam_lerp(a, b, t):
    t = ease(t)
    return (tuple(np.add(np.multiply(a[0], 1 - t), np.multiply(b[0], t))), tuple(np.add(np.multiply(a[1], 1 - t), np.multiply(b[1], t))),
            a[2] * (1 - t) + b[2] * t)


def movie(fast: bool = False) -> None:
    OUT.mkdir(exist_ok=True)
    mv = Movie()
    fps = mv.fps
    sec = (lambda s: max(2, int(s * fps * (0.5 if fast else 1.0))))
    wide = (FOCAL, ISO, 1900)
    load_cam = ((185, 120, 520), (0.25, 1.0, 0.45), 900)
    station_cam = ((95, 0, 320), (-0.35, 1.0, 0.12), 760)

    # 1. assembly from scratch (steps 1-8): parts fly in along their insertion offsets
    empty = L.State(loaded=(), station=False, ext=0.0)
    pl_all = L.placements(empty)
    for s in range(1, 9):
        n = sec(1.4 if s != 6 else 2.2)
        for i in range(n):
            t = ease(i / (n - 1))
            cur = [p for p in pl_all if p.step <= s]
            offs = {p.name: np.asarray(p.explode, float) * 3.0 * (1 - t) for p in cur if p.step == s}
            cols = {p.name: (0.75, 0.75, 0.78) for p in cur if p.step < s}
            mv.frame(cur, f"Assembly {s}/11: {L.STEP_TITLES[s]}", "", colors=cols, offsets=offs, cam=wide)
        mv.hold(sec(0.4))

    # 2. prepare a module: the auger into Sam's mounting plate, cap on (the "carrier" onto the auger)
    k_load = 3
    base = L.State(loaded=(), station=False, ext=0.0)
    for i in range(sec(2.0)):
        t = ease(i / (sec(2.0) - 1))
        st = L.State(loaded=(k_load,), station=False, ext=0.0, out_module=k_load, out_frac=1.0)
        pl = L.placements(st)
        offs = {}
        for p in pl:
            if p.module == k_load and p.key in ("auger", "auger_cap"):
                offs[p.name] = np.array([0.0, 0.0, 90.0]) * (1 - t) + (np.array([60.0, 0, 0]) * (1 - t) if p.key == "auger_cap" else 0)
        mv.frame(pl, "Module: slide the auger into Sam's mounting plate, screw on the cap", "the auger is the lab's threaded-storage auger (PR #170); the plate is Sam's Oct 13 part",
                 offsets=offs, cam=load_cam, hide={p.name for p in pl if p.key == "thumb_screw" and p.module == k_load})
    mv.hold(sec(0.5))

    # 3. load every module at the loading position, indexing one module between loads
    loaded: list[int] = []
    shift = K.HOME_SHIFT
    for j in range(N_MODULES):
        k = (k_load - j) % N_MODULES          # the gondola at the loading position after j indexes
        slow = j < 2
        n_in = sec(1.6 if slow else 0.6)
        for i in range(n_in):
            f = 1.0 - ease(i / (n_in - 1))
            st = L.State(shift=shift, loaded=tuple(loaded + [k]), station=False, ext=0.0, out_module=k, out_frac=f)
            mv.frame(L.placements(st), f"Load module {j + 1} of 12 at the loading position", "slide in, lower onto the gondola floor, two M5 thumb screws into Sam's knuckles",
                     cam=load_cam if slow else cam_lerp(load_cam, wide, 0.5))
        n_s = sec(0.8 if slow else 0.3)
        for i in range(n_s):
            t = ease(i / (n_s - 1))
            st = L.State(shift=shift, loaded=tuple(loaded + [k]), station=False, ext=0.0, thumb_out={k: 20.0 * (1 - t)})
            mv.frame(L.placements(st), f"Load module {j + 1} of 12 at the loading position", "thumb screws in: their tips are the hinge pins",
                     cam=load_cam if slow else cam_lerp(load_cam, wide, 0.5))
        loaded.append(k)
        if j == N_MODULES - 1:
            break
        n_i = sec(1.3 if slow else 0.5)
        for i in range(n_i):
            s = shift + MODULE_LINKS * scurve_shift(i, n_i - 1)
            mv.frame(L.placements(L.State(shift=s, loaded=tuple(loaded), station=False, ext=0.0)),
                     "Index one module: 10 links = 1250 motor steps", f"chain shift {s - K.HOME_SHIFT:5.1f} links",
                     cam=load_cam if slow else cam_lerp(load_cam, wide, 0.5))
        shift += MODULE_LINKS

    # 4. one full lap at speed (gondolas stay upright round every corner)
    allm = tuple(range(N_MODULES))
    n_lap = sec(6.0)
    for i in range(n_lap):
        s = shift + K.N_LINKS * scurve_shift(i, n_lap - 1)
        mv.frame(L.placements(L.State(shift=s, loaded=allm, station=False, ext=0.0)), "A full lap: every module stays upright, round the top and the corners",
                 f"chain shift {(s - K.HOME_SHIFT) % K.N_LINKS:5.1f} links", cam=cam_lerp(wide, ((160, 0, 470), (-1, 0.15, 0.1), 1700), i / (n_lap - 1)))
    shift += K.N_LINKS
    shift = K.station_shift(0) if abs(((shift - K.station_shift(0)) % K.N_LINKS)) < 1e-6 else shift

    # 5. station: index module 1 in, actuator lifts the carriage, docks, tilts, auger turns, back down
    s0 = shift % K.N_LINKS
    k_st = None
    for k in range(N_MODULES):
        if abs((K.station_shift(k) - s0) % K.N_LINKS) < 1e-6:
            k_st = k
    st_base = dict(shift=s0, loaded=allm)
    cut = cutaway(L.placements(L.State(ext=0.0, **st_base)), {k_st})
    for i in range(sec(1.5)):
        mv.frame(L.placements(L.State(ext=0.0, **st_base)), "Station: a module arrives mid-way along the bottom run", "",
                 cam=cam_lerp(wide, station_cam, i / (sec(1.5) - 1)))
    for i in range(sec(1.2)):
        e = 20.0 * ease(i / (sec(1.2) - 1))
        mv.frame(L.placements(L.State(ext=e, **st_base)), "Actuonix P16-P lifts the electronics carriage through the gondola floor",
                 f"approach {e:4.1f} mm in the fork (no tilt yet)", cam=station_cam, hide=cut)
    for i in range(sec(2.5)):
        a = 35.0 * ease(i / (sec(2.5) - 1))
        mv.frame(L.placements(L.State(tilt=max(a, 0.01), **st_base)), "Docked: plate and carriage tilt together about the hinge",
                 f"tilt {a:4.1f} deg (stroke used {L.actuator_pose(L.State(tilt=max(a, 0.01), **st_base), k_st if k_st is not None else 0, K.pivots(s0))[2] - L.ACT_RETRACTED:5.1f} mm)",
                 cam=station_cam, hide=cut)
    mv.hold(sec(0.3))
    pl_d = L.placements(L.State(tilt=35.0, **st_base))
    for i in range(sec(2.0)):
        spin = 2 * math.pi * 1.0 * i / fps          # the auger turning at 1 rev/s (60 rpm) while it doses
        for p in pl_d:
            if p.module == k_st and p.key in ("auger", "auger_cap"):
                p.M = p.M @ L.T(L.Rz(2 * math.pi / fps))
            if p.key == "pinion":
                p.M = p.M @ L.T(L.Rz(-2 * math.pi / fps * 44 / 20))
        mv.frame(pl_d, "Dosing at 35 deg: NEMA 11 turns the auger through 20T:44T, solenoid taps", f"auger {spin / (2 * math.pi):4.2f} rev",
                 cam=station_cam, hide=cut)
    for i in range(sec(1.5)):
        a = 35.0 * (1 - ease(i / (sec(1.5) - 1)))
        mv.frame(L.placements(L.State(tilt=max(a, 0.01), **st_base)), "Dose done: tilt back, carriage drops below the gondolas' path", f"tilt {a:4.1f} deg",
                 cam=station_cam, hide=cut)
    for i in range(sec(0.8)):
        e = 20.0 * (1 - ease(i / (sec(0.8) - 1)))
        mv.frame(L.placements(L.State(ext=e, **st_base)), "Dose done: tilt back, carriage drops below the gondolas' path", "", cam=station_cam, hide=cut)

    # 6. swap a module: index it to the loading position, thumb screws out, lift, slide out, new one in
    k_sw = k_st if k_st is not None else 0
    s_from, s_to = s0, K.load_shift(k_sw)
    d = (s_to - s_from) % K.N_LINKS
    n_i = sec(2.0)
    for i in range(n_i):
        s = s_from + d * scurve_shift(i, n_i - 1)
        mv.frame(L.placements(L.State(shift=s, loaded=allm, ext=0.0)), "Swap: bring the module to the loading position", f"{d / MODULE_LINKS:.0f} indexes",
                 cam=cam_lerp(station_cam, load_cam, i / (n_i - 1)))
    for i in range(sec(0.8)):
        t = ease(i / (sec(0.8) - 1))
        mv.frame(L.placements(L.State(shift=s_to, loaded=allm, ext=0.0, thumb_out={k_sw: 20.0 * t})), "Swap: unscrew the two thumb screws", "",
                 cam=load_cam)
    for i in range(sec(1.6)):
        f = ease(i / (sec(1.6) - 1))
        mv.frame(L.placements(L.State(shift=s_to, loaded=allm, ext=0.0, out_module=k_sw, out_frac=f)), "Swap: lift 22 mm, slide out sideways",
                 "the gondola stays on the chain", cam=load_cam)
    new_col = {}
    for i in range(sec(1.6)):
        f = 1 - ease(i / (sec(1.6) - 1))
        pl = L.placements(L.State(shift=s_to, loaded=allm, ext=0.0, out_module=k_sw, out_frac=f))
        new_col = {p.name: (0.1, 0.65, 0.35) for p in pl if p.module == k_sw and p.key in ("sam_mounting_plate", "auger_cap")}
        mv.frame(pl, "Swap: a different powder's module goes in", "", colors=new_col, cam=load_cam)
    for i in range(sec(0.8)):
        t = ease(i / (sec(0.8) - 1))
        mv.frame(L.placements(L.State(shift=s_to, loaded=allm, ext=0.0, thumb_out={k_sw: 20.0 * (1 - t)})), "Swap: thumb screws back in. Done",
                 "", colors=new_col, cam=load_cam)
    mv.hold(sec(1.5))

    # write MP4 + GIF
    import imageio.v2 as iio
    mp4 = OUT / "paternoster.mp4"
    w = iio.get_writer(mp4, fps=fps, codec="libx264", quality=7, macro_block_size=8, ffmpeg_params=["-pix_fmt", "yuv420p"])
    for im in mv.frames:
        w.append_data(np.asarray(im))
    w.close()
    gif_frames = [im.resize((720, 405), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE, colors=96) for im in mv.frames[::2]]
    gif_frames[0].save(OUT / "paternoster.gif", save_all=True, append_images=gif_frames[1:], duration=int(2000 / fps), loop=0, optimize=True)
    print(f"  {len(mv.frames)} frames -> {mp4.name} ({mp4.stat().st_size / 1e6:.1f} MB), paternoster.gif "
          f"({(OUT / 'paternoster.gif').stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--movie", action="store_true")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--fast", action="store_true")
    a = ap.parse_args()
    if a.quick:
        stills(quick=True)
    if a.stills:
        stills()
    if a.movie:
        movie(fast=a.fast)
