"""Render the tri-star clip on the project page: docs/static/videos/tristar_tilts.mp4.

The tri-star is the fixed-base multi-auger design in issue #204: three of today's
doser modules, without their servos and tilt gears, on one printed base round one
beaker, each tilted by its own Actuonix P16 linear actuator. It exists only in CAD.
This script animates the newest layout, L4 (24 Nov 2026): a P16-200 leaning 25°
out under each module, on a telescoping leg unit, with the shelf 340 mm above the
bench over the A&D HR-100A / HR-250AZ.

The geometry is #204's own: ``design/multi-auger-fixed-base/`` on the branch
``claude/issue-204-20261124-0505`` at 13c5154, which reads PR #170's STEP files of
the current doser at a pinned commit. This script only poses those parts, renders
them with VTK and labels the frames; it changes nothing in the design.

To rebuild (about 7 minutes; needs ffmpeg on the PATH, and offscreen OpenGL, e.g. libosmesa6 or libegl1):

    git fetch origin claude/issue-204-20261124-0505
    git worktree add --detach /tmp/wt204 13c5154
    python -m venv /tmp/venv204
    /tmp/venv204/bin/pip install cadquery trimesh python-fcl rtree vtk pillow numpy matplotlib scipy manifold3d requests
    /tmp/venv204/bin/python docs/static/make_tristar_clip.py /tmp/wt204/design/multi-auger-fixed-base

It writes docs/static/videos/tristar_tilts.mp4 and its poster,
docs/static/images/tristar_tilts.jpg.
"""
from __future__ import annotations

import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

STATIC = Path(__file__).resolve().parent
W, H = 1280, 720            # output frame
TOP, BOTTOM = 64, 58        # text bands
SS = 2                      # supersampling for the 3D view
FPS = 20
DATE = "CAD of 24 Nov 2026"


# --------------------------------------------------------------------------- #
# storyboard: (seconds, chapter, title, caption, tilts A/B/C, azimuth, elevation)
# A is the back module (bearing 90°), B the front-left (210°), C the front-right (330°).
# --------------------------------------------------------------------------- #
def ease(u: float) -> float:
    u = min(max(u, 0.0), 1.0)
    return u * u * (3.0 - 2.0 * u)


CHAPTERS = [
    ("1/4", "Three of today's modules round one beaker",
     "Each keeps its auger, cap, stepper and solenoid; the servos and tilt gears are gone. One printed base holds "
     "all three, 340 mm up on three telescoping legs over the balance."),
    ("2/4", "Each module tilts on its own linear actuator",
     "An Actuonix P16-200, leaning 25° out under each module, tilts it from 0 to 90° (the doses so far used 20-40°). "
     "The powders dose one at a time."),
    ("3/4", "All three reach 90° at once",
     "At 90° the modules come no closer to each other than 5.8 mm, between #203's tap brackets."),
    ("4/4", "From above: three outlets over one beaker",
     "The hinges are 32 mm from the beaker's axis, so the outlets sit on a 41 mm circle at 0° and a 64 mm circle "
     "at 90°: a 250 mL beaker (70 mm across) under them catches all three."),
]

DOSE = 40.0
PLAN_EL = 84.0


def timeline():
    """One entry per frame: (chapter index, (tA, tB, tC), az, el)."""
    frames = []

    def hold(n, ch, t, az0, az1, el0=18.0, el1=18.0):
        for i in range(n):
            u = i / max(n - 1, 1)
            frames.append((ch, t, az0 + (az1 - az0) * u, el0 + (el1 - el0) * ease(u)))

    az = -74.0
    # 1. all parked, slow turn
    hold(int(3.0 * FPS), 0, (0.0, 0.0, 0.0), az, az + 6.0)
    az += 6.0
    # 2. A, then B, then C, each up to the dose tilt, hold, and back
    for k in range(3):
        up, stay, down, gap = int(1.0 * FPS), int(0.7 * FPS), int(0.8 * FPS), int(0.25 * FPS)
        seq = [ease(i / (up - 1)) for i in range(up)] + [1.0] * stay + \
              [1.0 - ease(i / (down - 1)) for i in range(down)] + [0.0] * gap
        for j, s in enumerate(seq):
            t = [0.0, 0.0, 0.0]
            t[k] = DOSE * s
            frames.append((1, tuple(t), az + 4.0 * (j / len(seq)), 18.0))
        az += 4.0
    # 3. all three to 90 deg together, hold, back
    up, stay, down = int(1.6 * FPS), int(1.0 * FPS), int(1.4 * FPS)
    seq = [ease(i / (up - 1)) for i in range(up)] + [1.0] * stay + [1.0 - ease(i / (down - 1)) for i in range(down)]
    for j, s in enumerate(seq):
        frames.append((2, (90.0 * s,) * 3, az + 6.0 * (j / len(seq)), 18.0))
    az += 6.0
    # 4. rise to a plan view, hold, come back down to where the clip starts
    rise, stay, fall = int(1.6 * FPS), int(1.4 * FPS), int(1.6 * FPS)
    for i in range(rise):
        u = ease(i / (rise - 1))
        frames.append((3, (0.0, 0.0, 0.0), az + (-90.0 - az) * u, 18.0 + (PLAN_EL - 18.0) * u))
    for i in range(stay):
        frames.append((3, (0.0, 0.0, 0.0), -90.0, PLAN_EL))
    for i in range(fall):
        u = ease(i / (fall - 1))
        frames.append((3, (0.0, 0.0, 0.0), -90.0 + (-74.0 + 90.0) * u, PLAN_EL + (18.0 - PLAN_EL) * u))
    return frames


# --------------------------------------------------------------------------- #
# geometry from #204
# --------------------------------------------------------------------------- #
def load(design_dir: Path):
    sys.path.insert(0, str(design_dir))
    os.chdir(design_dir)
    import leg_unit as LU
    LU.prepare()
    import leg_unit_figs as F
    import doserlib as D
    import scale_room as SR
    import stands as ST
    S = 340.0
    zb = LU.BOT - S
    balance = D.Part("HR-100A", SR.hr_solid(True), SR.M_balance(90.0, zb), (0.80, 0.81, 0.83), "bal", False)
    bench = ST.bench(zb, half=330.0)

    def pose(tilts):
        parts = [p for p in F.station_parts(tilts, S=S, balance=False) if p.name != "bench"]
        return parts + [balance], bench

    return D, pose


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #
class Scene:
    def __init__(self, D):
        import vtk
        self.vtk, self.D = vtk, D
        self.cache = {}         # id(shape) -> (shape, vtkPolyData with normals)

    def poly(self, shape):
        vtk = self.vtk
        from vtkmodules.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
        k = id(shape)
        if k not in self.cache:
            m = self.D.mesh_of(shape)
            pts = vtk.vtkPoints()
            pts.SetData(numpy_to_vtk(np.ascontiguousarray(m.vertices, dtype=float), deep=True))
            cells = vtk.vtkCellArray()
            f = np.hstack([np.full((len(m.faces), 1), 3), m.faces]).astype(np.int64).ravel()
            cells.SetCells(len(m.faces), numpy_to_vtkIdTypeArray(f, deep=True))
            pd = vtk.vtkPolyData()
            pd.SetPoints(pts)
            pd.SetPolys(cells)
            nrm = vtk.vtkPolyDataNormals()
            nrm.SetInputData(pd)
            nrm.SetFeatureAngle(35.0)
            nrm.SplittingOn()
            nrm.Update()
            self.cache[k] = (shape, nrm.GetOutput())
        return self.cache[k][1]

    def vertices(self, parts):
        out = []
        for p in parts:
            v = np.asarray(self.D.mesh_of(p.shape).vertices)
            out.append(v @ p.M[:3, :3].T + p.M[:3, 3])
        return np.vstack(out)

    def render(self, parts, bench, focal, scale, az, el, size):
        vtk = self.vtk
        ren = vtk.vtkRenderer()
        ren.SetBackground(1.0, 1.0, 1.0)
        for p in parts + [bench]:
            mp = vtk.vtkPolyDataMapper()
            mp.SetInputData(self.poly(p.shape))
            a = vtk.vtkActor()
            a.SetMapper(mp)
            pr = a.GetProperty()
            pr.SetColor(*p.colour)
            pr.SetOpacity(p.opacity)
            pr.SetAmbient(0.28)
            pr.SetDiffuse(0.78)
            pr.SetSpecular(0.18)
            pr.SetSpecularPower(15)
            t = vtk.vtkTransform()
            t.SetMatrix([float(v) for v in p.M.reshape(-1)])
            a.SetUserTransform(t)
            ren.AddActor(a)
        cam = ren.GetActiveCamera()
        a_, e_ = math.radians(az), math.radians(el)
        d = np.array([math.cos(e_) * math.cos(a_), math.cos(e_) * math.sin(a_), math.sin(e_)])
        cam.SetFocalPoint(*focal)
        cam.SetPosition(*(np.asarray(focal) + 2000.0 * d))
        cam.SetViewUp(0, 0, 1)
        cam.ParallelProjectionOn()
        cam.SetParallelScale(scale)
        ren.ResetCameraClippingRange()
        for pos, inten in (((0.4, 0.6, 1.0), 0.85), ((-0.6, -0.2, 0.8), 0.35)):
            lt = vtk.vtkLight()
            lt.SetLightTypeToCameraLight()
            lt.SetPosition(*pos)
            lt.SetIntensity(inten)
            ren.AddLight(lt)
        win = vtk.vtkRenderWindow()
        win.SetOffScreenRendering(1)
        win.SetSize(*size)
        win.AddRenderer(ren)
        win.Render()
        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(win)
        w2i.ReadFrontBufferOff()
        w2i.Update()
        from vtkmodules.util.numpy_support import vtk_to_numpy
        img = w2i.GetOutput()
        wx, wy, _ = img.GetDimensions()
        arr = vtk_to_numpy(img.GetPointData().GetScalars()).reshape(wy, wx, -1)[::-1, :, :3]
        win.Finalize()
        return np.ascontiguousarray(arr)


def view_basis(az, el):
    a_, e_ = math.radians(az), math.radians(el)
    d = np.array([math.cos(e_) * math.cos(a_), math.cos(e_) * math.sin(a_), math.sin(e_)])
    up = np.array([0, 0, 1.0]) - d * d[2]
    up /= np.linalg.norm(up)
    rt = np.cross(d, up)            # screen right (camera looks along -d)
    return rt, up


# --------------------------------------------------------------------------- #
# labels, in the style of PR #185's clips
# --------------------------------------------------------------------------- #
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_M = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def font(path, size):
    from PIL import ImageFont
    return ImageFont.truetype(path, size)


def wrap(d, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    lines.append(cur)
    return lines


def label(im, ch, tilts):
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    tag, title, cap = CHAPTERS[ch]
    navy = (31, 56, 112)
    ft, fb, fs, fm = font(FONT_B, 17), font(FONT_B, 24), font(FONT, 16), font(FONT_M, 17)
    # chapter tag and title
    tw = d.textlength(tag, font=ft)
    d.rounded_rectangle([14, 16, 14 + tw + 16, 44], radius=5, fill=navy)
    d.text((22, 19), tag, font=ft, fill=(255, 255, 255))
    d.text((14 + tw + 28, 15), title, font=fb, fill=(25, 25, 25))
    d.line([14, 54, W - 14, 54], fill=(210, 214, 222), width=2)
    d.line([14, 54, 14 + 260, 54], fill=navy, width=3)
    small = font(FONT, 12)
    stamp = f"tri-star (L4) · #204 · {DATE}"
    d.text((W - 14 - d.textlength(stamp, font=small), 4), stamp, font=small, fill=(150, 150, 150))
    # tilt readout
    rows = [f"tilt  A {tilts[0]:4.1f}°", f"      B {tilts[1]:4.1f}°", f"      C {tilts[2]:4.1f}°"]
    bw = max(d.textlength(r, font=fm) for r in rows) + 24
    x0, y0 = W - 14 - bw, TOP + 10
    d.rounded_rectangle([x0, y0, W - 14, y0 + 12 + 24 * len(rows)], radius=6, fill=(28, 32, 40))
    for i, r in enumerate(rows):
        d.text((x0 + 12, y0 + 7 + 24 * i), r, font=fm, fill=(160, 240, 150))
    # module key
    fk = font(FONT, 15)
    key = ["A: back", "B: front left", "C: front right"]
    for i, k in enumerate(key):
        d.text((x0 + 4, y0 + 22 + 24 * len(rows) + 20 * i), k, font=fk, fill=(90, 90, 90))
    # colour key, bottom left above the caption
    items = [("today's parts", (0.50, 0.70, 0.90)), ("plate, gears off", (0.97, 0.77, 0.20)),
             ("#203's tap bracket", (0.85, 0.20, 0.55)), ("new base", (0.95, 0.47, 0.18)),
             ("leg unit", None), ("P16-200", (0.30, 0.32, 0.36))]
    return d, items


def finish(im, ch, tilts, leg_rgb):
    from PIL import ImageDraw
    d, items = label(im, ch, tilts)
    fk = font(FONT, 14)
    x, y = 16, H - BOTTOM - 24
    for name, col in items:
        rgb = leg_rgb if col is None else tuple(int(255 * c) for c in col)
        d.rectangle([x, y + 2, x + 13, y + 15], fill=rgb, outline=(60, 60, 60))
        d.text((x + 19, y), name, font=fk, fill=(60, 60, 60))
        x += 19 + d.textlength(name, font=fk) + 18
    d.rectangle([0, H - BOTTOM, W, H], fill=(244, 246, 250))
    d.line([0, H - BOTTOM, W, H - BOTTOM], fill=(220, 224, 230), width=1)
    fs = font(FONT, 16)
    lines = wrap(d, CHAPTERS[ch][2], fs, W - 40)
    for i, ln in enumerate(lines[:2]):
        d.text((18, H - BOTTOM + 9 + 21 * i), ln, font=fs, fill=(45, 45, 45))
    return im


# --------------------------------------------------------------------------- #
def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    design = Path(sys.argv[1]).resolve()
    only = int(sys.argv[2]) if len(sys.argv) > 2 else None      # render only every Nth frame (preview)
    from PIL import Image
    D, pose = load(design)
    sc = Scene(D)
    frames = timeline()
    print(f"{len(frames)} frames, {len(frames) / FPS:.1f} s", flush=True)

    # One focal point for the whole clip, and one scale for the 18° views and one for the plan, blended by
    # elevation while the camera rises and comes back, so nothing breathes while the modules tilt.
    vw, vh = W, H - TOP - BOTTOM - 30
    samples = []
    for f in frames[:: max(1, FPS // 4)]:
        parts, _ = pose(f[1])
        samples.append((f[3], sc.vertices(parts)) + view_basis(f[2], f[3]))
    allv = np.vstack([s_[1] for s_ in samples])
    focal = (allv.max(0) + allv.min(0)) / 2

    def need(v, rt, up):
        w = (v - focal) @ rt
        h = (v - focal) @ up
        return max(np.abs(h).max(), np.abs(w).max() * vh / vw)

    low = max(need(v, rt, up) for el, v, rt, up in samples if el < 18.5) * 1.03
    plan = max(need(v, rt, up) for el, v, rt, up in samples if el > PLAN_EL - 0.5) * 1.03

    def scale_at(el):
        u = (el - 18.0) / (PLAN_EL - 18.0)
        return low + (plan - low) * min(max(u, 0.0), 1.0)
    leg_rgb = None

    out = Path(tempfile.mkdtemp(prefix="tristar-"))
    for i, (ch, tilts, az, el) in enumerate(frames):
        if only and i % only:
            continue
        parts, bench = pose(tilts)
        if leg_rgb is None:
            leg = next(p for p in parts if p.name.endswith("leg head"))
            leg_rgb = tuple(int(255 * c) for c in leg.colour)
        arr = sc.render(parts, bench, focal, scale_at(el), az, el, (vw * SS, vh * SS))
        view = Image.fromarray(arr).resize((vw, vh), Image.LANCZOS)
        im = Image.new("RGB", (W, H), "white")
        im.paste(view, (0, TOP))
        finish(im, ch, tilts, leg_rgb).save(out / f"f{i:04d}.png")
        if i % 40 == 0:
            print(f"  frame {i}", flush=True)

    mp4 = STATIC / "videos" / "tristar_tilts.mp4"
    jpg = STATIC / "images" / "tristar_tilts.jpg"
    if only:
        print("preview frames in", out)
        return
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(out / "f%04d.png"),
                    "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(mp4)], check=True)
    Image.open(out / "f0000.png").convert("RGB").save(jpg, quality=86)
    shutil.rmtree(out)
    print("wrote", mp4, mp4.stat().st_size, "bytes;", jpg)


if __name__ == "__main__":
    main()
