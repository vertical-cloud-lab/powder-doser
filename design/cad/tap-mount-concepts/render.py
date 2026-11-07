"""Render the issue #203 tapper concepts on PR #170's current-design assembly.

    xvfb-run -a python3 render.py     # -> renders/*.png, step/*.step

Needs PR #170's cad/full-assembly (fetched and unpacked at the pinned commit
by ``concepts.ensure_pr170`` if PR170_FULL_ASSEMBLY doesn't point at it).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import cadquery as cq
import numpy as np
import vtk
from PIL import Image, ImageDraw, ImageFont

import concepts as C

C.ensure_pr170()
sys.path.insert(0, str(C.FA / "onshape"))
import layout  # noqa: E402  (PR #170)

COMP = C.FA / "components"
OUT = C.OUT
OUT.mkdir(exist_ok=True)
C.STEP_OUT.mkdir(exist_ok=True)

KEEP = ["Baseplate", "Mounting plate", "Auger", "Auger cap", "Stepper pinion", "Stepper (NEMA 11)",
        "Servo pinion (+X)", "Servo pinion (-X)", "Servo MG996R (+X)", "Servo MG996R (-X)"]
OLD = ["Bracket (rear)", "Bracket (front)", "Tap collar base (AI)", "Tap collar", "Solenoid (Adafruit 412)"]

COL = {
    "Baseplate": (0.62, 0.66, 0.72), "Mounting plate": (0.80, 0.82, 0.86),
    "Auger": (0.90, 0.76, 0.45), "Auger cap": (0.30, 0.45, 0.80),
    "Stepper pinion": (0.45, 0.70, 0.55), "Stepper (NEMA 11)": (0.30, 0.30, 0.35),
    "Servo pinion (+X)": (0.50, 0.85, 0.55), "Servo pinion (-X)": (0.50, 0.85, 0.55),
    "Servo MG996R (+X)": (0.20, 0.20, 0.22), "Servo MG996R (-X)": (0.20, 0.20, 0.22),
    "Bracket": (0.55, 0.72, 0.85), "Bracket (rear)": (0.55, 0.72, 0.85),
    "Bracket (front)": (0.55, 0.72, 0.85),
    "Tap collar base (AI)": (0.55, 0.40, 0.70), "Tap collar": (0.70, 0.45, 0.85),
    "Solenoid (Adafruit 412)": (0.60, 0.62, 0.66), "Solenoid": (0.60, 0.62, 0.66),
    "printed": (0.70, 0.45, 0.85), "hardware": (0.76, 0.77, 0.80),
}

_cache: dict = {}


def polydata(shape) -> vtk.vtkPolyData:
    pd = shape.toVtkPolyData(0.04, 0.2)
    n = vtk.vtkPolyDataNormals()
    n.SetInputData(pd)
    n.SetFeatureAngle(35.0)
    n.SplittingOn()
    n.Update()
    return n.GetOutput()


def step_pd(rel: str):
    if rel not in _cache:
        shp = cq.importers.importStep(str(COMP / rel))
        _cache[rel] = polydata(cq.Compound.makeCompound(shp.vals()))
    return _cache[rel]


def L_to_world(tilt: float = 0.0) -> np.ndarray:
    """4x4 taking concept (L) coordinates to the world at a given tilt."""
    tilt_m = (layout.T(None, (0, layout.HINGE_Y, layout.HINGE_Z)) @ layout.rot_about(layout.X, tilt)
              @ layout.T(None, (0, -layout.HINGE_Y, -layout.HINGE_Z)))
    return tilt_m @ layout.MP @ layout.T(None, tuple(C.L2MP))


def colour_for(name: str):
    if "printed" in name:
        return COL["printed"]
    if "M3" in name:
        return COL["hardware"]
    return COL.get(name, (0.7, 0.7, 0.7))


def scene(concept: int | None, auger_lift: float = 0.0, opacity_old=1.0, extra=None):
    """[(polydata, colour, 4x4, opacity)] for the assembly with a concept."""
    items = []
    places = layout.placements(0.0)
    lift = layout.T(None, (0, 0, auger_lift))
    for name in KEEP:
        rel, M = places[name]
        if name in ("Auger", "Auger cap"):
            M = lift @ M
        items.append((step_pd(rel), COL[name], M, 1.0))
    Lw = L_to_world()
    if concept is None:          # the current design, from PR #170
        for name in OLD:
            rel, M = places[name]
            items.append((step_pd(rel), COL[name], M, opacity_old))
        return items
    # Flexible brackets on both bracket rows (concept 2 replaces the front one)
    rows = [-124.0 - C.TAP_ROW_MP_X] + ([] if concept == 2 else [C.FRONT_BRACKET_X])
    for rx in rows:
        items.append((polydata(C.bracket_in_L(rx).val()), COL["Bracket"], Lw, 1.0))
    for name, wp in C.CONCEPTS[concept][1]().items():
        items.append((polydata(wp.val()), colour_for(name), Lw, 1.0))
    for (wp, col, op) in (extra or []):
        items.append((polydata(wp.val()), col, Lw, op))
    return items


def vtk_matrix(M):
    t = vtk.vtkTransform()
    t.SetMatrix([float(v) for v in np.asarray(M).reshape(-1)])
    return t


def render(items, path: Path, cam: dict, size=(1100, 820)):
    ren = vtk.vtkRenderer()
    ren.SetBackground(1.0, 1.0, 1.0)
    for pd, col, M, op in items:
        m = vtk.vtkPolyDataMapper()
        m.SetInputData(pd)
        a = vtk.vtkActor()
        a.SetMapper(m)
        p = a.GetProperty()
        p.SetColor(*col)
        p.SetOpacity(op)
        p.SetSpecular(0.3)
        p.SetSpecularPower(15)
        a.SetUserTransform(vtk_matrix(M))
        ren.AddActor(a)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(*size)
    win.AddRenderer(ren)
    if any(op < 1 for *_, op in items):
        ren.SetUseDepthPeeling(1)
        win.SetAlphaBitPlanes(1)
        win.SetMultiSamples(0)
    c = ren.GetActiveCamera()
    c.SetFocalPoint(*cam["focal"])
    c.SetPosition(*cam["pos"])
    c.SetViewUp(0, 0, 1)
    c.SetViewAngle(cam.get("angle", 30))
    ren.ResetCameraClippingRange()
    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.SetScale(2)
    w2i.ReadFrontBufferOff()
    w2i.Update()
    w = vtk.vtkPNGWriter()
    w.SetFileName(str(path))
    w.SetInputConnection(w2i.GetOutputPort())
    w.Write()
    print("  ->", path.name)


# camera on the tap zone, from the outlet end, the side away from the stepper, above
TAP_W = (L_to_world() @ np.array([0, 0, 0, 1.0]))[:3]
FOCAL = TAP_W + np.array([18.0, -5.0, -6.0])
CAM = {"focal": tuple(FOCAL), "pos": tuple(FOCAL + np.array([215.0, -175.0, 165.0])), "angle": 30}
CAM_SWAP = {"focal": tuple(FOCAL + np.array([-5, 10, 22])),
            "pos": tuple(FOCAL + np.array([-5, 10, 22]) + np.array([235.0, -205.0, 150.0])), "angle": 30}

TITLES = {
    0: "Now: tap collar rides on the tube",
    1: "1  Bolt-on tap tower",
    2: "2  Tap bracket (front clip + tower, one part)",
    3: "3  See-saw hammer, strikes from below",
    4: "4  Flip-away saddle (old collar, hinged)",
    5: "Swap with 2: the auger lifts straight out",
}


def font(sz):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if Path(f).exists():
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def board(paths: list[Path], titles: list[str], out: Path, cols=3):
    ims = [Image.open(p).convert("RGB") for p in paths]
    w, h = ims[0].size
    w2, h2 = w // 2, h // 2
    rows = math.ceil(len(ims) / cols)
    pad = 70
    sheet = Image.new("RGB", (cols * w2, rows * (h2 + pad)), "white")
    d = ImageDraw.Draw(sheet)
    f = font(30)
    for i, (im, t) in enumerate(zip(ims, titles)):
        r, c = divmod(i, cols)
        x, y = c * w2, r * (h2 + pad)
        sheet.paste(im.resize((w2, h2), Image.LANCZOS), (x, y + pad))
        d.text((x + 18, y + 18), t, fill=(20, 20, 20), font=f)
        d.rectangle([x + 2, y + 2, x + w2 - 3, y + h2 + pad - 3], outline=(200, 200, 200), width=2)
    sheet.save(out, optimize=True)
    print("  ->", out.name)


def main():
    paths, titles = [], []
    for k in (0, 1, 2, 3, 4):
        p = OUT / f"concept{k}.png"
        render(scene(None if k == 0 else k), p, CAM)
        paths.append(p)
        titles.append(TITLES[k])
    # swap: concept 2 with the auger and cap lifted 45 mm out of the clips
    p = OUT / "concept2_swap.png"
    render(scene(2, auger_lift=45.0), p, CAM_SWAP)
    paths.append(p)
    titles.append(TITLES[5])
    board(paths, titles, OUT / "concepts_board.png")
    # flip saddle open (ghost) next to closed
    ghost = [(wp, colour_for(n), 0.35) for n, wp in C.concept4(open_deg=75.0).items() if "post" not in n and "pin" not in n]
    render(scene(4, extra=ghost), OUT / "concept4_open.png", CAM)
    # STEP of the printed parts, in L (auger axis = x, plate floor top at y = -29.25)
    for k in (1, 2, 3, 4):
        for n, wp in C.CONCEPTS[k][1]().items():
            if "printed" in n:
                slug = n.split(" (")[0].lower().replace(" ", "-")
                cq.exporters.export(wp, str(C.STEP_OUT / f"concept{k}-{slug}.step"))
    cq.exporters.export(C.flexible_bracket(), str(C.STEP_OUT / "flexible-bracket-recreation.step"))
    print("  -> step/*.step")


if __name__ == "__main__":
    main()
