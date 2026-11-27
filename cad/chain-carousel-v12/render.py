"""Renders and animations of the chain-carousel test rig (VTK, offscreen under xvfb-run). v11 uses the stills and the step images; the
movie, the feature clips and the scale fit below are still v4's (v11's clips are explain11.py, rail_profile.py and chain_nitro.py).

    xvfb-run -a python render.py --stills      # v11's stills (renders/rig_*.png: still_views()), then one image per assembly step
                                               #   (renders/steps/step_NN.png) and renders/assembly_steps.gif
    xvfb-run -a python render.py --stills --only rig_iso,rig_tilt90    # just these stills
    xvfb-run -a python render.py --steps       # only the assembly steps and the GIF (--steps 8,12: just those steps, no GIF)
    xvfb-run -a python render.py --quick       # rig_iso only
    xvfb-run -a python render.py --movie       # v4: assembly from scratch, modules onto carriages, carriages onto the chain
                                               #   one index at a time, a lap, the station cycle, the hatches, a swap
                                               #   -> renders/chain_carousel_v4.mp4 and .gif
    xvfb-run -a python render.py --features    # v4: one short GIF + MP4 per new feature (renders/features/)

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
from params import (CHAIN_L, PARK_DROP, DOOR_TRAVEL, HOOK_SLIDE, LATCH_TRAVEL, MODULE_LINKS, N_LINKS, N_MODULES, P, RUN_DIRECTION, SCREW_OUT,
                    TILT_DOSE_WORLD, HATCH_OPEN_DEG)
DOCK_EXT = PARK_DROP

SEEK_MM, SEEK_REV_S = 3.0, 0.25          # docking seek (gear-mesh study): pinion turning through the last 3 mm, magnet on
MAG_GAP_DESIGN = 0.15                    # mm, dock magnet face under the steel tab when docked
MAG_F_DESIGN = 20.0 / (1 + MAG_GAP_DESIGN / 0.4) ** 2   # 10.6 N: the gear-mesh study's law for the P20/15 on a 2 mm tab
CENTRE_DIST = 32.25                      # pinion to 44T gear when docked (params.NEMA11_Z)

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache"
OUT = HERE / "renders"
FINE = ("chain", "sprocket", "m3", "insert", "magnet", "nut", "eclip", "clevis_pin", "pinion", "hall", "kc_", "vee_dowel", "door_", "latch_",
        "flat_pad", "m2x8")
TAG = "chain carousel v4, #128"


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


def default_opacity(p) -> float:
    """Acrylic and glass are see-through (and outlined); the HR-100A is drawn as a ghost where it has to stand (it collides
    with the station there: see the scale-fit study)."""
    if p.key.startswith(("panel_", "hatch_", "bay9_", "baffle9_", "deck9", "bay10_", "baffle10_", "deck10_")):
        return 0.22
    if p.key == "hr100a_body":
        return 0.40
    if p.key in ("hr100a_glass", "beaker"):
        return 0.25
    if p.key in BAL11_SEE:                 # v11: the tall cage's glass, its doors and the dosing lid, so the pillar and beaker show
        return 0.2
    return 1.0


BAL11_SEE = ("bal11_glass", "bal11_door_left", "bal11_door_right", "bal11_lid")
OUTLINED = ("panel_", "hatch_", "hr100a_body", "hr100a_glass", "bay9_", "baffle9_", "deck9", "bay10_", "baffle10_", "deck10_") + BAL11_SEE
TINT = {"hr100a_body": (0.50, 0.56, 0.68), "hr100a_glass": (0.55, 0.75, 0.90)}
for _k in ("panel_side", "panel_side_hatch", "panel_front_hatch", "panel_back", "panel_top", "hatch_front", "hatch_side", "panel_front_bay", "panel_front_door11",
           "bay9_front", "bay9_top", "bay9_side_p", "bay9_side_m", "bay9_door", "baffle9_side_p", "baffle9_side_m", "baffle9_back", "deck9",
           "bay10_front", "bay10_top", "bay10_side_p", "bay10_side_m", "baffle10_side_p", "baffle10_side_m", "baffle10_back", "deck10_front",
           "deck10_riser", "deck10_back"):
    TINT[_k] = (0.60, 0.76, 0.90)


def outline(pd: vtk.vtkPolyData) -> vtk.vtkPolyData:
    """Boundary and sharp-feature edges of a part, for drawing see-through parts' outlines."""
    fe = vtk.vtkFeatureEdges()
    fe.SetInputData(pd)
    fe.BoundaryEdgesOn()
    fe.FeatureEdgesOn()
    fe.SetFeatureAngle(40)
    fe.ManifoldEdgesOff()
    fe.NonManifoldEdgesOff()
    fe.Update()
    return fe.GetOutput()


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
        self.ren.SetUseDepthPeeling(1)
        self.ren.SetMaximumNumberOfPeels(6)
        self.win.SetAlphaBitPlanes(1)
        self.actors: dict[str, vtk.vtkActor] = {}
        self.outlines: dict[str, vtk.vtkActor] = {}

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
            op_k = (opacity.get(k, opacity.get(p.name, default_opacity(p))) if opacity else default_opacity(p))
            if p.key.startswith(OUTLINED) or op_k < 0.9:
                ol = self.outlines.get(k)
                if ol is None:
                    om = vtk.vtkPolyDataMapper()
                    om.SetInputData(outline(_PD[p.key]))
                    om.ScalarVisibilityOff()
                    ol = vtk.vtkActor()
                    ol.SetMapper(om)
                    ol.GetProperty().SetColor(0.35, 0.42, 0.5)
                    ol.GetProperty().SetLineWidth(1.4)
                    ol.GetProperty().SetLighting(False)
                    self.outlines[k] = ol
                    self.ren.AddActor(ol)
                ol.SetUserMatrix(vmat(M))
                ol.VisibilityOn()
            col = colors.get(k, colors.get(p.name, TINT.get(p.key, p.color))) if colors else TINT.get(p.key, p.color)
            a.GetProperty().SetColor(*col)
            a.GetProperty().SetOpacity(opacity.get(k, opacity.get(p.name, default_opacity(p))) if opacity else default_opacity(p))
            a.VisibilityOn()
            seen.add(k)
        for k, a in self.actors.items():
            if k not in seen:
                a.VisibilityOff()
        for k, a in self.outlines.items():
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
    """Title (wrapped to the image's width: v11's step titles are long) and the step's BoM lines on a white band above the render."""
    ft = font(34)
    meas = ImageDraw.Draw(img)
    tl, cur = [], ""
    for w in title.split():
        t = f"{cur} {w}".strip()
        if cur and meas.textlength(t, font=ft) > img.width - 56:
            tl.append(cur)
            cur = w
        else:
            cur = t
    tl.append(cur)
    band = 70 + 42 * (len(tl) - 1) + 30 * len(lines) + 12
    out = Image.new("RGB", (img.width, img.height + band), (255, 255, 255))
    out.paste(img, (0, band))
    d = ImageDraw.Draw(out)
    for i, t in enumerate(tl):
        d.text((28, 18 + 42 * i), t, fill=(20, 20, 20), font=ft)
    y = 66 + 42 * (len(tl) - 1)
    for ln in lines:
        d.text((30, y), ln, fill=(70, 70, 70), font=font(22))
        y += 30
    d.line((0, band - 1, img.width, band - 1), fill=(210, 210, 210), width=2)
    return out


P16_OUTSIDE11 = ("bar11", "m5x35_shcs", "p16_bracket11", "grommet10")   # v11: the front bar, the P16's clevis, the grommet in the plate


def front_open(p: L.Placement) -> bool:
    """Hide the front side plate, everything bolted outside it and the enclosure, to look straight at the front chain loop. v11: the
    P16-150 (its base is outside the plate, its rod inside), its clevis, the front bar and the grommet go as a whole, so nothing floats."""
    return (p.key == "side_plate_front" or (p.M[0, 3] < -30.5 and p.key not in ("ext_x", "foot", "board_panel") and p.group not in ("scale",))
            or (p.key == "m5x12_bhcs" and p.M[0, 3] < -29.0) or p.group in ("enclosure", "scale", "station_act") or p.key in P16_OUTSIDE11)


def no_enclosure(p: L.Placement) -> bool:
    return p.group == "enclosure"


def station_cut(p: L.Placement) -> bool:
    """Station close-ups: hide the enclosure, the balance, the -y half of the frame, the carriages away from the station
    and the front plate."""
    if front_open(p) or p.group in ("enclosure", "scale"):
        return True
    if p.key in ("ext_post", "ext_x", "corner_bracket", "tnut_m5", "m5x12_bhcs", "standoff", "standoff_back") and p.M[1, 3] < 0:
        return True
    return p.module not in (-1, 0) and p.module >= 0 and abs(p.M[1, 3] - L.STATION_Y) > 50


def station_cut_y(p: L.Placement) -> bool:
    """Station cutaway: station_cut, plus the station carriage, its chain links and the module's plate on the -y side of
    the station's centre plane are kept; the frame's -y members and everything at y < -40 go."""
    if station_cut(p):
        return True
    return p.group in ("frame", "plates") and p.M[1, 3] < -40


H = L.HINGE_STATION
D = L.DOSE_POINT
HERO = ((160, 0, 430), (-0.9, -1.0, 0.55), 2250)
LOOP = ((120, 0, 510), (-1.0, -0.42, 0.22), 1400)
STATION = ((H[0] + 45, H[1], H[2] - 40), (-0.5, -1.0, 0.05), 600)
STATION_TILT = ((H[0] + 70, H[1], H[2] + 25), (-0.35, -1.0, 0.2), 780)
DOCK = ((H[0] + 50, H[1], H[2] - 20), (-0.25, -1.0, -0.30), 270)
DOOR = ((D[0] - 2, D[1] - 4, D[2] - 4), (-1.0, -0.75, -0.25), 150)
LATCH = ((H[0] + 112, H[1] - 19, H[2] + 12), (0.55, -0.75, -0.75), 200)
LATCH_BELOW = ((H[0] + 126, H[1] - 22, H[2] - 18), (-0.2, -1.0, -0.6), 190)
CRADLE = ((H[0] + 40, H[1], H[2] - 85), (-0.5, -1.0, 0.25), 360)
LOADC = ((150, 140, float(L.load_frame()[2, 3]) - 5.0), (0.35, 1.0, 0.35), 1050)
SIDE_HATCH = ((150, 170, float(L.load_frame()[2, 3]) - 30.0), (0.25, 1.0, 0.3), 1350)
FRONT_HATCH = ((-60, 5, 200), (-1.0, -0.55, 0.3), 1250)
SCALE = ((D[0] - 30, D[1], 230), (-0.75, -1.0, 0.35), 950)
TAB = tuple(L.to_world(L.load_frame(), (0.0, L.CAR_W0, L.A1_HOLE_C)))


def dock_cut(p: L.Placement) -> bool:
    """Dock and door close-ups: station_cut, plus the cradle, the front hold-down, the sprockets and shafts, the front chain,
    and the station carriage itself (it sits over the dock)."""
    if station_cut(p):
        return True
    if p.key in ("carriage", "m3x12_bhcs", "nut_m3", "magnet", "latch_bolt", "latch_follower", "latch_spring") and p.module == 0:
        return True
    if p.key in ("cradle", "hold_down", "hall_switch", "sprocket_32", "shaft", "shaft_drive", "flange_bearing", "ext_cradle_post", "vee_dowel") and \
            not (p.key == "vee_dowel" and p.group == "station_ec"):
        return True
    if p.key in ("m5x16_shcs", "insert_m5") and p.M[0, 3] < 0:
        return True
    return p.key.startswith("chain") and p.M[0, 3] < 20


def latch_cut(p: L.Placement) -> bool:
    return station_cut(p) or p.key in ("ext_latch_post", "ext_cradle_post", "cradle", "sprocket_32", "shaft", "shaft_drive", "auger", "auger_cap",
                                       "nema34", "m5x25_shcs", "nut_m5", "sprocket_15_motor", "sprocket_15_shaft", "lrs350", "cl86t") or p.group == "drive"


def ghost_plate(pl, op=0.35):
    """Module 1's plate, auger and door housing see-through, so the dock's balls and seats show."""
    return {k: op for k, p in keyed(pl) if p.module == 0 and p.key in ("sam_mounting_plate", "auger", "door_housing", "auger_cap", "carriage")}


def ghost_cradle(pl, op=0.35):
    return {k: op for k, p in keyed(pl) if p.key == "cradle"}


def hidden(pl, fn) -> set:
    return {k for k, p in keyed(pl) if fn(p)} if fn else set()


# ---------------------------------------------------------------- stills (v11)
HERO11 = ((172.0, 0.0, 385.0), (-0.9, -1.0, 0.55), 2100)                 # the whole rig from the front left, above
LOOP11 = ((150.0, 0.0, 505.0), (-1.0, -0.42, 0.22), 1450)                # the front chain loop (front plate hidden)
BACK11 = ((400.0, 130.0, 300.0), (1.0, 0.75, 0.45), 2350)                # the back: the NEMA 34, the drive chain, the board behind
LOAD11 = ((172.0, 140.0, float(L.load_frame()[2, 3]) - 5.0), (0.35, 1.0, 0.35), 1100)    # the loading position, from +y
HATCH11 = ((172.0, 150.0, float(L.load_frame()[2, 3]) - 60.0), (0.25, 1.0, 0.3), 1550)   # the side hatch, from +y
STEP8_11 = ((140.0, 5.0, 450.0), (-0.35, -1.0, 0.05), 1150)             # the station inside the loop, from -y under the beam (no carriages yet)
STEP1_11 = ((172.0, 0.0, 60.0), (-0.9, -1.0, 0.75), 1350)               # the base frame on the bench
STEP11_11 = ((600.0, 180.0, 150.0), (0.45, 1.0, 0.8), 1700)             # the electronics board behind the rig
DROP11 = ((73.4, 4.8, 300.0), (-0.25, -1.0, 0.08), 340)                 # the exit, the dosing lid and the beaker on its pillar


def latch_cut11(p: L.Placement) -> bool:
    """v6's latch close-up (explain6.latch) for v11: carriage 1 with its plate and latch, the cam, the chain and the frame; the augers, the
    EC and the P16, the back plate (behind the cam), the NEMA 34, the drive, the balance and the other carriages go."""
    return (p.group in ("enclosure", "elec", "scale", "station_ec", "station_act", "drive") or p.key in ("auger", "auger_cap", "side_plate_back", "nema34")
            or (p.module not in (-1, 0) and p.group in ("modules", "carriages")))


def _wide(cam, f: float = 1.25):
    """explain11's cameras are framed for its 1280 x 574 viewport; a still is 1600 x 1000 (narrower for its height): step back."""
    return (cam[0], cam[1], cam[2] * f)


def still_views() -> list:
    """v11's stills: (name, state, camera, hide, title, sub, opacity). The cut-aways, close-up cameras and see-through parts are
    explain11's (the clips in renders/v11/), so each still shows the same parts its clip does."""
    import explain11 as X                   # lazily: explain11 imports this module
    from params import LATCH10_RAMP_DEG, LATCH_RAIL_FLAT, LATCH_Y6, SOL11_X
    op = X.opac
    no_elec = lambda p: p.group == "elec"                                                          # noqa: E731
    p16_cut = lambda p: p.group in ("enclosure", "elec", "scale") or (p.module >= 0 and p.module != 0)   # noqa: E731
    e0, e30, e90 = (L.p16_11_ext(a) for a in (0.0, 30.0, 90.0))
    gear_cut = lambda p: X.close_cut(p) or p.key in ("solenoid", "door_head11", "door_rod11")    # noqa: E731
    # the latch from the front (its follower is 35 mm in front of the back plate), carriage 1 and its plate see-through
    LATCH11 = (tuple(L.to_world(L.sam_frame(L.station_frame(), 0.0), (262.0, LATCH_Y6, -6.0))), (-1.0, -0.5, -0.3), 190)
    ghost_latch = lambda pl: {k: 0.35 for k, p in keyed(pl) if p.module == 0 and p.key in ("carriage", "sam_mounting_plate")}   # noqa: E731
    ramp_end = LATCH_RAIL_FLAT + LATCH_TRAVEL / math.tan(math.radians(LATCH10_RAMP_DEG))     # 25.8 mm: where a follower meets the cam
    S0 = dict(enclosure=False)
    before = -RUN_DIRECTION                 # a positive shift: carriage 1 still on its way in (the machine runs -1)
    return [
        ("rig_iso", L.State(), HERO11, no_elec, "Chain carousel v11: the station inside the loop (0-90 deg), the carousel lowered over a tall-cage balance",
         "13 modules outside the loop; the acrylic enclosure with the balance's open doorway in front; the side hatch (+y) for swaps", op),
        ("rig_open", L.State(**S0), HERO11, no_elec, "v11 without its enclosure: module 1 at the station under EC v11; the P16-150 through the front plate",
         "carriages 40 mm longer (chains 345 mm apart); the balance with its tall cage on the bench, the beaker on a pillar", op),
        ("rig_loop", L.State(), LOOP11, lambda p: front_open(p) or no_elec(p), "Front chain loop (the front plate, the P16 and the enclosure hidden)",
         "13 carriages on two Nitro RC35 chains, 345 mm apart, their modules outside the loop; 32T sprockets on four shafts", op),
        ("rig_station", L.State(**S0), _wide(X.CAM_SIDE), X.near_cut, "Station at rest: EC v11 on module 1, inside the loop; the module rests on its own carriage",
         f"the P16-150 fully out ({e0:.1f} of 150 mm) from its clevis outside the front plate (the beam and the EC's guide cut away)", op),
        ("rig_tilt30", L.State(tilt=30.0, **S0), _wide(X.CAM_SIDE_HI), X.near_cut, "Dosing at 30 deg: the P16 pulls the EC and module 1 up about the hinge",
         f"P16 {e30:.1f} of 150 mm out; the exit is on the hinge axis, so it doesn't move", op),
        ("rig_tilt90", L.State(tilt=90.0, **S0), _wide(X.CAM_SIDE_HI), X.near_cut, "90 deg: the hinge 73 mm behind the front chain leaves the module and the EC room",
         f"P16 {e90:.1f} of 150 mm out; the EC passes the carriage's opening by 2.5 mm, the solenoid the carriage by 2.5 mm", op),
        ("rig_p16", L.State(**S0), _wide(X.CAM_FRONT, 1.45), p16_cut, "Outside the front plate: the P16-150's clevis under a new 2020 bar across the front posts",
         "two M5 into T-nuts in the bar; the P16 through a 22 x 68 mm slot in the front side plate; the grommet hole under it",
         lambda pl: op(pl, {"side_plate_front": 0.6})),
        ("rig_rail", L.State(**S0), _wide(X.CAM_RAIL), X.close_cut, "The straight rail: the plate's T-bracket in the EC's slot (level lips, flared ends; no lift)",
         "at rest the T's head is 0.2 mm over the lips: the module sits on its carriage, the lips take it only when the P16 pulls",
         lambda pl: op(pl, {"ec11": 0.6})),
        ("rig_gear", L.State(**S0), _wide(X.CAM_GEAR), gear_cut, "The 44T gear meets the 24T pinion at rest (the EC see-through)",
         "the hinge is 5 mm nearer the carriage, so the gear pokes past it; centre distance 34.25 mm",
         lambda pl: op(pl, {"ec11": 0.35, "sam_mounting_plate": 0.5, "t_bracket": 0.6, "door_housing": 0.5})),
        ("rig_door_open", L.State(**S0), _wide(X.CAM_DOOR), X.close_cut, "Outlet door open: the EC's front ramp holds the rod's head 6 mm toward the loop",
         "a 1.5 mm stainless rod from the shutter up the spring's axis, through the housing's cap, to a printed head; no cable",
         lambda pl: op(pl, {"ec11": 0.7})),
        ("rig_door_closed", L.State(shift=before * 3.0, **S0), _wide(X.CAM_DOOR), X.close_cut,
         "Outlet door shut: module 1 three links before the station, its head not yet in the ramp",
         "the spring holds the shutter over the 3 mm exit; the door is fully open within 7 mm of the station",
         lambda pl: op(pl, {"ec11": 0.7})),
        ("rig_solenoid", L.State(**S0), _wide(X.CAM_SOL), X.close_cut, f"The solenoid over clip 1, {SOL11_X:.0f} mm behind the exit (the auger's first third)",
         "in a collar in the EC's spine, its plunger 1.2 mm off the plate; it turns with the module, so it taps the same spot at every tilt",
         lambda pl: op(pl, {"ec11": 0.5})),
        ("rig_latch", L.State(**S0), LATCH11, latch_cut11, f"Plate latch at the station: the cam holds carriage 1's bolt {LATCH_TRAVEL:g} mm back, its pin out of the keeper",
         f"the cam on an arm from the back side plate (hidden), its +-{LATCH_RAIL_FLAT:.0f} mm flat and {LATCH10_RAMP_DEG:.0f} deg ramps; carriage 1 and its plate see-through, the augers hidden", ghost_latch),
        ("rig_latch_closed", L.State(shift=before * 4.0, **S0), LATCH11, latch_cut11, "Half an index before the station: carriage 1's bolt is home, its pin in the keeper",
         f"its follower meets the cam's ramp {ramp_end:.1f} mm from the station; carriage 1 and its plate see-through, the augers hidden", ghost_latch),
        ("rig_balance", L.State(), _wide(X.CAM_BAL, 1.15), lambda p: no_elec(p) or p.key == "panel_side",
         "The balance with its tall draft cage (315 mm) on the bench, through the front panel's open doorway",
         "the carousel is 98.5 mm lower than v10's: the passing 44T gears clear the cage's top by 4 mm; no bay window, no chamber",
         lambda pl: op(pl, {"panel_front_door11": 0.25, "panel_side_hatch": 0.12, "panel_top": 0.1, "panel_back": 0.1, "beaker": 1.0})),
        ("rig_drop", L.State(tilt=30.0, **S0), DROP11, X.near_cut,
         f"The dose falls {X.DROP:.0f} mm from the exit through the dosing lid's 24 mm hole into the beaker",
         "the lid sits in the cage's top frame in place of the top door; the beaker stands on a printed 40 mm pillar on the pan",
         lambda pl: op(pl, {"bal11_frame": 0.16, "beaker": 1.0})),   # opaque: translucent, it is lost behind the cage glass (6 peels)
        ("rig_side_hatch", L.State(hatch_side=HATCH_OPEN_DEG), HATCH11, no_elec, "The side hatch (+y) open: swaps at the loading position",
         "3 mm acrylic on standoffs outside the 2020 frame; the front has an open doorway for the balance instead of a hatch", op),
        ("rig_load", L.State(out_auger=3, auger_out=120.0, hatch_side=HATCH_OPEN_DEG), LOAD11, no_elec,
         "Swap through the side hatch: module 4's auger comes straight off its plate",
         "the side tabs take the pull, not the chain; the door, plate and carriage stay on the chain (check_interference.py --swap)", op),
        ("rig_side_tabs", L.State(), (TAB, (-0.6, 1.0, -0.2), 240), front_open, "Side tab at the loading position: its foot 1 mm outside the tongue", "", op),
        ("rig_back_iso", L.State(), BACK11, None, "Back: the NEMA 34 inside the frame drives the bottom +y shaft; the electronics board behind",
         "", op),
    ]


def stills(quick: bool = False, only: tuple = ()) -> None:
    """v11's stills -> renders/rig_*.png (`only`: just these names); then the assembly steps (renders/steps/, assembly_steps.gif)."""
    OUT.mkdir(exist_ok=True)
    v = View()
    views = still_views()
    if quick:
        views = views[:1]
    elif only:
        views = [x for x in views if x[0] in only]
    for name, st, cam, hide_fn, title, sub, op_fn in views:
        pl = L.placements(st)
        v.show(pl, hide=hidden(pl, hide_fn), opacity=op_fn(pl) if op_fn else None)
        v.camera(*cam)
        caption(v.image(), title, sub, "chain carousel v11 · PR #185").save(OUT / f"{name}.png")
        print("  wrote", name, flush=True)
    if quick or only:
        return
    step_images(v)


def step_images(v: View | None = None, only: tuple = ()) -> None:
    """One image per layout.STEPS step (renders/steps/step_NN.png) and renders/assembly_steps.gif: the parts of earlier steps pale, the
    step's own parts in colour, lifted along the way they go in (Placement.explode), with the step's BoM lines (bom.step_lines) above."""
    import bom
    v = v or View()
    items = bom.step_lines()
    STEP = OUT / "steps"
    STEP.mkdir(parents=True, exist_ok=True)
    pl = L.placements(L.State())
    cams = {1: STEP1_11, 2: HERO11, 3: HERO11, 4: ((172.0, 0.0, 530.0), (-0.9, -1.0, 0.45), 1750), 5: LOOP11, 6: ((380.0, 60.0, 360.0), (1.0, 0.85, 0.3), 1200),
            7: LOOP11, 8: STEP8_11, 9: LOOP11, 10: LOOP11, 11: STEP11_11, 12: HERO11}
    frames = []
    for s in sorted(L.STEPS):
        cur = [p for p in pl if p.step <= s]
        hide = hidden(cur, (lambda p: p.step < s and front_open(p))) if s in (5, 7, 9, 10) else set()
        if s == 8:                          # the -y side of the frame, between the camera and the station inside the loop
            hide |= hidden(cur, lambda p: p.step < s and p.group == "frame" and p.key != "ext_y" and p.M[1, 3] < -100.0)
        colors = {k: tuple(0.55 + 0.45 * c for c in p.color) for k, p in keyed(cur) if p.step < s}
        offs = {k: np.asarray(p.explode, float) for k, p in keyed(cur) if p.step == s}
        if only and s not in only:
            continue
        v.show(cur, colors=colors, offsets=offs, hide=hide)
        v.camera(*cams[s])
        img = caption_lines(v.image(), f"Step {s}. {L.STEPS[s]}", items.get(s, [])[:14])
        img.save(STEP / f"step_{s:02d}.png")
        frames.append(img)
        print("  step", s, flush=True)
    if only:
        return
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
        self._emit(caption(self.v.image(), title, sub, TAG))

    def hold(self, n):
        if self.last is not None:
            for _ in range(n):
                self._emit(self.last)

    def close(self) -> None:
        self.writer.close()


def _bench_module(mv, sec, k0, cam):
    """A v3 module put together on the bench, then pinned onto its carriage; the latch closes over the plate's keeper."""
    bench = dict(carriages=(k0,), modules=(k0,), ext=0.0, out_carriage=k0, out_slide=HOOK_SLIDE, out_lift=170.0, screws_out=SCREW_OUT,
                 enclosure=False, scale=False)
    pl_b = L.placements(L.State(**bench))
    Cb = next(p.M for p in pl_b if p.key == "carriage" and p.module == k0)
    u_dir, w_dir = Cb[:3, 0], Cb[:3, 1]
    away = w_dir * 110.0
    module_keys = ("sam_mounting_plate", "flat_pad_v4", "auger", "auger_cap", "kc_ball", "door_housing", "door_shutter", "door_spring",
                   "m2x8_shcs")

    def pins_out(p, t):
        su = 1.0 if float(u_dir @ (p.M[:3, 3] - Cb[:3, 3])) > 0 else -1.0
        return su * u_dir * 40.0 * (1 - t)

    beats = [("Module: the lab auger into the v4 mounting plate (Sam's Oct 13 plate + auger-side dock balls, keeper)", "threaded-storage auger and cap (PR #170)",
              lambda p, t: (away + (np.array([-170.0 * (1 - t), 0, 0]) if p.key in ("auger", "auger_cap") else 0.0)) if p.key in module_keys
              else pins_out(p, 0.0)),
             ("Module: two 1/4 in steel balls pressed into the plate's auger side, a steel washer flush beside them",
              "the plate's half of the kinematic dock: the EC's cone and vee take the balls, its third ball sits on the washer",
              lambda p, t: (away - (w_dir * 25.0 * (1 - t) if p.key in ("kc_ball", "flat_pad_v4") else 0.0)) if p.key in module_keys
              else pins_out(p, 0.0)),
             ("Module: the outlet door: housing, shutter and spring on the plate's front", "the spring holds the shutter over the 3 mm exit",
              lambda p, t: (away + (np.array([-40.0 * (1 - t), 0, 0]) if p.key in ("door_housing", "door_shutter", "door_spring", "m2x8_shcs") else 0.0))
              if p.key in module_keys else pins_out(p, 0.0)),
             ("Module: onto a carriage's OUTER face, between its hinge lugs; the latch's pin slides into the plate's keeper",
              "the carriage is the module's mount on the chain", lambda p, t: away * (1 - t) if p.key in module_keys else pins_out(p, 0.0)),
             ("Module: two 5 mm clevis pins through the lugs into the plate's knuckles, e-clips on", "",
              lambda p, t: pins_out(p, t) if p.key in ("clevis_pin", "eclip") else None)]
    for title, sub, off_fn in beats:
        n = sec(1.5)
        for i in range(n):
            t = ease(i / (n - 1))
            pl = L.placements(L.State(**bench))
            offs = {}
            for k, p in keyed(pl):
                if p.module == k0 and (p.key in module_keys or p.key in ("clevis_pin", "eclip")):
                    o = off_fn(p, t)
                    if o is not None:
                        offs[k] = np.asarray(o, float)
            mv.frame(pl, title, sub, offsets=offs, cam=cam)
        mv.hold(sec(0.3))


def _station_cycle(mv, sec, cam=None, title_prefix="Station", spin0=0.0, extra_state=None):
    """The v3 station cycle at the station: rise in the guide, the door opens, seat on the dock, magnet on, tilt, dose,
    tilt back, reverse a turn, magnet off, undock, park. Returns nothing; frames go to mv."""
    xs = dict(extra_state or {})
    tf = L.frame_dose_tilt(TILT_DOSE_WORLD)
    cam_s = cam or STATION
    hide = station_cut

    def S(**kw):
        d = dict(xs)
        d.update(kw)
        return L.State(**d)
    n = sec(1.0)
    for i in range(n):
        mv.frame(L.placements(S(ext=0.0)), f"{title_prefix}: the EC parked in its guide cradle, {PARK_DROP:.0f} mm under its dock",
                 "the station's rail has drawn carriage 1's latch pin back; its module rests 0.5 mm down on the tube rest", cam=cam_s, hide_fn=hide)
    n = sec(2.4)
    for i in range(n):
        e = DOCK_EXT * ease(i / (n - 1))
        door = max(0.0, DOOR_TRAVEL - (DOCK_EXT - e))
        sub = "the guide's side and front walls keep it square" if door <= 0 else f"its finger lifts the outlet door: {door:4.1f} of {DOOR_TRAVEL} mm"
        mv.frame(L.placements(S(ext=e, magnet_on=e > DOCK_EXT - 2.0)), f"{title_prefix}: the P16 lifts the EC out of the cradle ({e:4.1f} mm)", sub,
                 cam=cam_s, hide_fn=hide)
    n = sec(1.0)
    for i in range(n):
        mv.frame(L.placements(S(magnet_on=True)), f"{title_prefix}: seated on the kinematic dock, round the auger",
                 "plate balls in the cone and the vee, the EC's ball C on the washer; the door is open; the module is off its tube rest", cam=cam_s,
                 hide_fn=hide)
    n = sec(2.0)
    for i in range(n):
        a = tf * ease(i / (n - 1))
        mv.frame(L.placements(S(tilt=a, magnet_on=True, spin=spin0)), f"{title_prefix}: tilt; module and EC turn up through the carriage's opening",
                 f"tilt {a:4.1f} deg", cam=cam_lerp(cam_s, STATION_TILT, i / (n - 1)) if cam is None else cam_s, hide_fn=hide)
    n = sec(2.2)
    for i in range(n):
        sp = spin0 + 2 * math.pi * 1.0 * i / (n - 1)
        tap = 2.0 if (i // 3) % 2 == 0 and i > n * 0.6 else 0.0
        mv.frame(L.placements(S(tilt=tf, magnet_on=True, spin=sp, tap=tap)),
                 f"{title_prefix}: dose at {TILT_DOSE_WORLD:.0f} deg straight into the beaker (no funnel)",
                 "the NEMA 11 turns the auger through the 20T pinion and the 44T gear; solenoid taps", cam=STATION_TILT if cam is None else cam_s,
                 hide_fn=hide)
    mv.hold(sec(0.4))
    n = sec(1.5)
    for i in range(n):
        a = tf * (1 - ease(i / (n - 1)))
        mv.frame(L.placements(S(tilt=a, magnet_on=True, spin=spin0 + 2 * math.pi)), f"{title_prefix}: hold 0.5 s, tilt back to level",
                 f"tilt {a:4.1f} deg", cam=cam_lerp(STATION_TILT, cam_s, i / (n - 1)) if cam is None else cam_s, hide_fn=hide)
    n = sec(1.2)
    for i in range(n):
        sp = spin0 + 2 * math.pi * (1 - i / (n - 1))
        mv.frame(L.placements(S(magnet_on=True, spin=sp)), f"{title_prefix}: at rest, reverse the auger one turn",
                 "pulls powder back from the exit before the door closes", cam=cam_s, hide_fn=hide)
    n = sec(2.0)
    for i in range(n):
        e = DOCK_EXT * (1 - ease(i / (n - 1)))
        door = max(0.0, DOOR_TRAVEL - (DOCK_EXT - e))
        mv.frame(L.placements(S(ext=e, spin=spin0)), f"{title_prefix}: the P16 lowers the module back onto its tube rest and parks the EC",
                 f"the door shuts first ({door:4.1f} mm open); the latch closes as the carriage leaves", cam=cam_s, hide_fn=hide)


def movie(fast: bool = False) -> None:
    OUT.mkdir(exist_ok=True)
    mp4 = OUT / "chain_carousel_v4.mp4"
    mv = Movie(mp4)
    fps = mv.fps
    sec = (lambda s: max(2, int(s * fps * (0.5 if fast else 1.0))))
    dirn = RUN_DIRECTION
    none = ()

    # 1. assembly from scratch: frame, plates, bearings, shafts, drive, chains, station (steps 1-8)
    pl_all = L.placements(L.State(carriages=none, modules=none, ext=0.0, enclosure=False, scale=False))
    for s in range(1, 9):
        n = sec(1.2 if s not in (7, 8) else 2.0)
        cam = HERO if s != 8 else cam_lerp(HERO, STATION, 0.6)
        for i in range(n):
            t = ease(i / (n - 1))
            cur = [p for p in pl_all if p.step <= s]
            offs = {k: np.asarray(p.explode, float) * 3.0 * (1 - t) for k, p in keyed(cur) if p.step == s}
            cols = {k: (0.75, 0.75, 0.78) for k, p in keyed(cur) if p.step < s}
            title, _, sub = L.STEPS[s].partition(": ")
            mv.frame(cur, f"Assembly {s}/12: {title}", sub, colors=cols, offsets=offs, cam=cam)
        mv.hold(sec(0.4))

    # 2. a module on the bench
    k0 = 3
    _bench_module(mv, sec, k0, LOADC)

    # 3. carriages onto the chain at the loading position, past the side tabs, one index at a time
    loaded: list[int] = []
    shift = 0.0
    base = dict(enclosure=False, scale=False)
    for j in range(N_MODULES):
        k = (k0 + j) % N_MODULES
        slow = j < 2
        cam = LOADC if slow else cam_lerp(LOADC, HERO, 0.55)
        n_in = sec(1.3 if slow else 0.4)
        for i in range(n_in):
            f = 1.0 - ease(i / (n_in - 1))
            st = L.State(shift=shift, carriages=tuple(loaded + [k]), modules=tuple(loaded + [k]), ext=0.0, out_carriage=k, out_slide=HOOK_SLIDE,
                         out_lift=170.0 * f, screws_out=SCREW_OUT, **base)
            mv.frame(L.placements(st), f"Carriage {j + 1} of 13 onto the chain at the loading position", "in sideways, 10 mm up from position",
                     cam=cam)
        n_s = sec(0.8 if slow else 0.3)
        for i in range(n_s):
            t = ease(i / (n_s - 1))
            st = L.State(shift=shift, carriages=tuple(loaded + [k]), modules=tuple(loaded + [k]), ext=0.0, out_carriage=k,
                         out_slide=HOOK_SLIDE * (1 - min(1, 2 * t)), out_lift=0.0, screws_out=SCREW_OUT * (1 - max(0, 2 * t - 1)), **base)
            mv.frame(L.placements(st), f"Carriage {j + 1} of 13 onto the chain at the loading position",
                     "slide 10 mm down: the hooks take the A-1 tabs and the tongues go into the side tabs; two M3 screws", cam=cam)
        loaded.append(k)
        if j == N_MODULES - 1:
            break
        n_i = sec(1.0 if slow else 0.4)
        for i in range(n_i):
            s_ = shift + dirn * MODULE_LINKS * scurve(i, n_i - 1)
            mv.frame(L.placements(L.State(shift=s_, carriages=tuple(loaded), modules=tuple(loaded), ext=0.0, **base)),
                     "Index one module: 8 links = 1000 motor steps", "bottom run toward -y", cam=cam)
        shift += dirn * MODULE_LINKS

    # 4. carriage 1 to the station, then a lap
    n_i = sec(0.8)
    for i in range(n_i):
        s_ = shift + dirn * MODULE_LINKS * scurve(i, n_i - 1)
        mv.frame(L.placements(L.State(shift=s_, ext=0.0, **base)), "Index: carriage 1 to the station", "", cam=cam_lerp(LOADC, HERO, 0.55))
    n_lap = sec(5.0)
    for i in range(n_lap):
        s_ = dirn * N_LINKS * scurve(i, n_lap - 1)
        mv.frame(L.placements(L.State(shift=s_, ext=0.0, **base)), "A full lap: every module rolls once; under the bottom run its latch pin holds the plate",
                 "each latch opens only while its carriage passes the station's rail", cam=cam_lerp(HERO, LOOP, i / (n_lap - 1)), hide_fn=front_open)

    # 5. the enclosure and the balance (step 12)
    pl12 = L.placements(L.State(ext=0.0))
    n = sec(2.0)
    for i in range(n):
        t = ease(i / (n - 1))
        offs = {k: np.asarray(p.explode, float) * 3.0 * (1 - t) for k, p in keyed(pl12) if p.step == 12}
        mv.frame(pl12, "Assembly 12/12: the acrylic enclosure and the HR-100A", "panels on standoffs; the balance is drawn where it has to stand",
                 offsets=offs, cam=HERO)

    # 6. the station cycle
    for i in range(sec(1.0)):
        mv.frame(L.placements(L.State(ext=0.0)), "How it works: one dose", "", cam=cam_lerp(HERO, STATION, i / (sec(1.0) - 1)), hide_fn=station_cut)
    _station_cycle(mv, sec)

    # 7. the hatches and a swap through the side hatch
    for i in range(sec(1.0)):
        mv.frame(L.placements(L.State(ext=0.0)), "The front hatch: the beaker's way in", "", cam=cam_lerp(STATION, FRONT_HATCH, i / (sec(1.0) - 1)))
    n = sec(1.4)
    for i in range(n):
        a = HATCH_OPEN_DEG * ease(i / (n - 1))
        mv.frame(L.placements(L.State(ext=0.0, hatch_front=a)), "Front hatch open: put a beaker on the scale's pan, close it",
                 "v4 can't put the HR-100A under the dose point yet either (README, item 6)", cam=FRONT_HATCH)
    for i in range(n):
        a = HATCH_OPEN_DEG * (1 - ease(i / (n - 1)))
        mv.frame(L.placements(L.State(ext=0.0, hatch_front=a)), "Front hatch closed", "", cam=FRONT_HATCH)
    for i in range(sec(1.0)):
        mv.frame(L.placements(L.State(ext=0.0)), "The side hatch: swaps at the loading position", "", cam=cam_lerp(FRONT_HATCH, SIDE_HATCH, i / (sec(1.0) - 1)))
    for i in range(n):
        a = HATCH_OPEN_DEG * ease(i / (n - 1))
        mv.frame(L.placements(L.State(ext=0.0, hatch_side=a)), "Side hatch open", "", cam=SIDE_HATCH)
    hs = dict(ext=0.0, hatch_side=HATCH_OPEN_DEG, out_auger=k0)
    for title, sub, fn in (("Swap: pull the auger straight off its plate, through the hatch", "the side tabs take the pull, not the chain",
                            lambda t: dict(auger_out=140.0 * t)),):
        nn = sec(1.6)
        for i in range(nn):
            t = ease(i / (nn - 1))
            mv.frame(L.placements(L.State(**hs, **fn(t))), title, sub, cam=SIDE_HATCH)
    for title in ("Swap: a different powder's auger clips into the same plate",):
        nn = sec(1.6)
        for i in range(nn):
            t = ease(i / (nn - 1))
            pl = L.placements(L.State(**hs, auger_out=140.0 * (1 - t)))
            new_col = {k: (0.1, 0.65, 0.35) for k, p in keyed(pl) if p.module == k0 and p.key in ("auger", "auger_cap")}
            mv.frame(pl, title, "door, plate and carriage stay on the chain", colors=new_col, cam=SIDE_HATCH)
    for i in range(n):
        a = HATCH_OPEN_DEG * (1 - ease(i / (n - 1)))
        mv.frame(L.placements(L.State(ext=0.0, hatch_side=a)), "Side hatch closed", "", cam=SIDE_HATCH)
    mv.hold(sec(1.2))
    mv.close()
    gif = OUT / "chain_carousel_v4.gif"
    mv.gif[0].save(gif, save_all=True, append_images=mv.gif[1:], duration=int(1000 * mv.GIF_EVERY / fps), loop=0, optimize=True)
    print(f"  {mv.n} frames ({mv.n / fps:.1f} s) -> {mp4.name} ({mp4.stat().st_size / 1e6:.1f} MB), {gif.name} ({gif.stat().st_size / 1e6:.1f} MB)")


# ---------------------------------------------------------------- feature GIFs
FEAT = OUT / "features"


class Clip(Movie):
    """A short feature clip: MP4 + GIF at 640 x 360 (GIF every 2nd frame)."""

    def __init__(self, name, w=1280, h=720, fps=12):
        FEAT.mkdir(parents=True, exist_ok=True)
        self.name = name
        super().__init__(FEAT / f"{name}.mp4", w, h, fps)
        self.GIF_EVERY = 2

    def _emit(self, img):
        self.writer.append_data(np.asarray(img))
        if self.n % self.GIF_EVERY == 0:
            self.gif.append(img.resize((640, 360), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE, colors=96))
        self.n += 1
        self.last = img

    def done(self):
        self.close()
        g = FEAT / f"{self.name}.gif"
        self.gif[0].save(g, save_all=True, append_images=self.gif[1:], duration=int(1000 * self.GIF_EVERY / self.fps), loop=0, optimize=True)
        print(f"  {self.name}: {self.n} frames, {g.stat().st_size / 1e6:.1f} MB", flush=True)


def features(only: str = "") -> None:
    sec = lambda s: max(2, int(s * 12))  # noqa: E731
    tf = L.frame_dose_tilt(TILT_DOSE_WORLD)

    if not only or only == "dock":
        c = Clip("dock_kinematic_coupling")
        for i in range(sec(4.0)):
            e = DOCK_EXT * ease(i / (sec(4.0) - 1))
            pl = L.placements(L.State(ext=e, magnet_on=e > DOCK_EXT - 2))
            c.v.show(pl, hide=hidden(pl, dock_cut), opacity=ghost_plate(pl))
            c.v.camera(*DOCK)
            c._emit(caption(c.v.image(), "Kinematic dock (item 1, v4): the EC's arms reach past the auger to the plate's balls",
                            f"cone and vee with N52 magnets behind them, ball C on a steel washer; {DOCK_EXT - e:4.1f} mm to go", TAG))
        for i in range(sec(1.0)):
            c._emit(c.last)
        c.done()
    if not only or only == "guide":
        c = Clip("guide_cradle")
        for i in range(sec(2.5)):
            e = DOCK_EXT * (1 - ease(i / (sec(2.5) - 1)))
            pl = L.placements(L.State(ext=e))
            c.v.show(pl, hide=hidden(pl, station_cut), opacity=ghost_cradle(pl))
            c.v.camera(*CRADLE)
            c._emit(caption(c.v.image(), "Guide (item 2): the EC drops back into its cradle and onto its own cone-vee-flat seat",
                            "side walls 0.3 mm off its body, a front wall it leans on; no back wall, so the tilt carries it out backward", TAG))
        for i in range(sec(3.0)):
            s_ = RUN_DIRECTION * MODULE_LINKS * scurve(i, sec(3.0) - 1)
            pl = L.placements(L.State(shift=s_, ext=0.0))
            c.v.show(pl, hide=hidden(pl, station_cut), opacity=ghost_cradle(pl))
            c.v.camera(*cam_lerp(CRADLE, STATION, 0.6))
            c._emit(caption(c.v.image(), f"Parked {PARK_DROP:.0f} mm under its dock, the EC lets the modules index past", "", TAG))
        c.done()
    if not only or only == "door":
        c = Clip("outlet_door")
        for phase, n, fn in (("rise", sec(3.0), lambda t: dict(ext=DOCK_EXT * t)), ("tilt", sec(2.0), lambda t: dict(tilt=tf * t, magnet_on=True)),
                             ("back", sec(1.5), lambda t: dict(tilt=tf * (1 - t), magnet_on=True)), ("down", sec(2.5), lambda t: dict(ext=DOCK_EXT * (1 - t)))):
            for i in range(n):
                t = ease(i / (n - 1))
                st = L.State(**fn(t))
                pl = L.placements(st)
                c.v.show(pl, hide=hidden(pl, dock_cut), opacity={k: 0.45 for k, p in keyed(pl) if p.key == "door_housing" and p.module == 0})
                c.v.camera(*DOOR)
                c._emit(caption(c.v.image(), "Outlet door (item 4): the docked EC's finger pushes the shutter toward the plate; its spring shuts it",
                                f"door {L.door_open(st):4.1f} of {DOOR_TRAVEL} mm open: only while the EC holds the module", TAG))
        c.done()
    if not only or only == "latch":
        c = Clip("plate_latch_v4")
        n = sec(5.0)
        for i in range(n):
            s_ = RUN_DIRECTION * (-6.0 + 12.0 * i / (n - 1))
            st = L.State(shift=s_, ext=0.0)
            pl = L.placements(st)
            k = L.carriage_at(L.CARRIAGE_LINK0, 0.0)
            c.v.show(pl, hide=hidden(pl, latch_cut))
            c.v.camera(*LATCH)
            lo = L.latch_open(k, st)
            c._emit(caption(c.v.image(), "Plate latch (item 4a): the station's rail draws the pin out of the keeper as the carriage arrives",
                            f"pin {lo:3.1f} of {LATCH_TRAVEL} mm back; the module rests on the tube rest meanwhile", TAG))
        topcam = ((150, 0, float(L.Z_TOP) + 40), (-0.5, -1.0, 0.1), 650)
        for i in range(sec(3.0)):
            s_ = RUN_DIRECTION * (N_LINKS / 2 - 4 + 8 * i / (sec(3.0) - 1))
            pl = L.placements(L.State(shift=s_, ext=0.0))
            c.v.show(pl, hide=hidden(pl, front_open))
            c.v.camera(*topcam)
            c._emit(caption(c.v.image(), "On the top run the modules sit on top of the loop, held by their hinges and latch pins", "", TAG))
        c.done()
    if not only or only == "hatches":
        c = Clip("enclosure_hatches")
        for nm, cam, key in (("front", FRONT_HATCH, "hatch_front"), ("side", SIDE_HATCH, "hatch_side")):
            for rng in ((0, 1), (1, 0)):
                n = sec(1.6)
                for i in range(n):
                    t = ease(i / (n - 1))
                    a = HATCH_OPEN_DEG * (rng[0] + (rng[1] - rng[0]) * t)
                    pl = L.placements(L.State(ext=0.0, **{key: a}))
                    c.v.show(pl)
                    c.v.camera(*cam)
                    c._emit(caption(c.v.image(), f"Enclosure (item 5): the {nm} hatch",
                                    "3 mm acrylic on standoffs outside the 2020 frame; stainless hinges, magnetic catch", TAG))
        c.done()
    if not only or only == "swap":
        c = Clip("side_tabs_swap")
        for title, fn in (("Side tabs (item 5a): the tongues sit 1 mm inside their feet at the loading position", lambda t: dict()),
                          ("Pull the auger off its plate: the clamps let go, the tabs take the pull (item 7)", lambda t: dict(auger_out=140.0 * t)),
                          ("A different powder's auger clips onto the same plate", lambda t: dict(auger_out=140.0 * (1 - t)))):
            n = sec(1.8)
            for i in range(n):
                t = ease(i / (n - 1))
                pl = L.placements(L.State(ext=0.0, hatch_side=HATCH_OPEN_DEG, out_auger=3, **fn(t)))
                c.v.show(pl)
                c.v.camera(*LOADC)
                c._emit(caption(c.v.image(), title, "", TAG))
        c.done()
    if not only or only == "outside":
        c = Clip("outside_loop")
        n = sec(5.0)
        for i in range(n):
            s_ = RUN_DIRECTION * N_LINKS / 4 * scurve(i, n - 1)
            pl = L.placements(L.State(shift=s_, ext=0.0, enclosure=False, scale=False))
            c.v.show(pl, hide=hidden(pl, front_open))
            c.v.camera(*LOOP)
            c._emit(caption(c.v.image(), "Item 7: the augers ride outside the loop, on their carriages' outer faces",
                            "the chain side of each carriage is v3's; the module, its hinge lugs and latch are on the other face", TAG))
        for i in range(sec(1.0)):
            pl = L.placements(L.State(ext=0.0, enclosure=False, scale=False))
            c.v.show(pl, hide=hidden(pl, station_cut))
            c.v.camera(*cam_lerp(LOOP, STATION, i / (sec(1.0) - 1)))
            c._emit(caption(c.v.image(), "At the station the module hangs under the bottom run", "", TAG))
        _station_cycle(c, sec)
        c.done()
    if not only or only == "cycle":
        c = Clip("how_it_works_station")
        _station_cycle(c, sec)
        c.done()


def scale_contacts(dxs=None) -> dict:
    """For every part the HR-100A meets with its pan under the dose point (checks/scale.json), how far in front of the
    dose point (mm, along -x) the balance first touches it when it slides in from the front. Bisection on the OCC
    common volume; cached in checks/scale_contacts.json."""
    import json
    import check_interference as CI
    cache = HERE / "checks" / "scale_contacts.json"
    if cache.exists():
        return json.loads(cache.read_text())
    rec = json.loads((HERE / "checks" / "scale.json").read_text())
    names = sorted({h["b"] for h in rec["clashes"]})
    pl = L.placements(L.State(ext=0.0))
    by_name: dict[str, list] = {}
    for p in pl:
        if p.name in names:
            by_name.setdefault(p.name, []).append(p)
    sc = [p for p in pl if p.group == "scale" and p.key != "beaker"]

    def hits(name, dx):
        objs = CI.objects([L.Placement(p.key, p.name, L.T(None, (dx, 0, 0)) @ p.M, p.step) for p in sc]) + CI.objects(by_name[name])
        n = len(sc)
        pairs = [(a, b) for a in range(n) for b in range(n, len(objs))]
        return bool(CI.overlaps(objs, pairs, min_vol=0.5))
    out = {}
    for nm in names:
        lo, hi = -500.0, 0.0                       # no contact at lo (balance 500 mm in front), contact at hi
        if hits(nm, lo):
            out[nm] = lo
            continue
        for _ in range(9):
            mid = (lo + hi) / 2
            if hits(nm, mid):
                hi = mid
            else:
                lo = mid
        out[nm] = round(hi, 1)
        print(f"  {nm}: first touched {-hi:.0f} mm before the dose point", flush=True)
    cache.write_text(json.dumps(out, indent=1) + "\n")
    return out


def scale_fit() -> None:
    """Item 6's GIF: the HR-100A slides in from the front toward the dose point; every part it would have to pass
    through turns red when it first touches it; then the list of what is in the way."""
    contacts = scale_contacts()
    c = Clip("scale_fit")
    cam = ((L.DOSE_POINT[0] - 90, L.DOSE_POINT[1] + 10, 200), (-1.0, -0.62, 0.38), 1150)
    hide_fn = lambda p: (p.group == "enclosure" or (p.group in ("frame", "plates", "elec") and p.M[1, 3] < -60 and p.key not in ("ext_y",))  # noqa: E731
                         or p.group == "elec" or (p.module >= 0 and abs(p.M[1, 3] - L.STATION_Y) > 60))
    bal = {"hr100a_body": (0.55, 0.62, 0.72), "hr100a_glass": (0.70, 0.85, 0.95), "hr100a_pan": (0.6, 0.6, 0.62)}
    n = sec_ = 12 * 7
    first = min(contacts.values()) if contacts else -100.0
    for i in range(n + 1):
        dx = -460.0 * (1 - ease(i / n))
        st = L.State(ext=0.0, scale_offset=(dx, 0.0))
        pl = L.placements(st)
        red = {k: (0.9, 0.12, 0.1) for k, p in keyed(pl) if p.name in contacts and dx >= contacts[p.name]}
        red.update({k: bal[p.key] for k, p in keyed(pl) if p.key in bal})
        op = {k: (0.75 if p.key == "hr100a_body" else 0.35) for k, p in keyed(pl) if p.group == "scale"}
        c.v.show(pl, colors=red, hide=hidden(pl, hide_fn), opacity=op)
        c.v.camera(*cam)
        hit = sum(1 for nm, v in contacts.items() if dx >= v)
        c._emit(caption(c.v.image(), "Scale (item 6): the A&D HR-100A slides in toward the dose point",
                        f"pan centre {-dx:5.0f} mm in front of the dose point; {hit} parts in its way (red)", TAG))
    c.hold(12)
    groups = [("the EC, its guide cradle and the P16 under the station", ("Electronics carriage", "NEMA 11", "pinion", "Guide cradle", "Cradle post",
                                                                         "Actuonix", "Actuator base clevis", "Station rail", "Dowel", "Magnet",
                                                                         "Shoulder screw", "M3 locknut")),
              ("the frame's front base cross rail", ("Base cross rail front",))]   # v4's wider frame clears the posts and the hold-down
    pl = L.placements(L.State(ext=0.0))
    red = {k: (0.9, 0.12, 0.1) for k, p in keyed(pl) if p.name in contacts}
    red.update({k: bal[p.key] for k, p in keyed(pl) if p.key in bal})
    op = {k: (0.5 if p.key == "hr100a_body" else 0.3) for k, p in keyed(pl) if p.group == "scale"}
    for title, keys in groups:
        if not any(nm.startswith(keys) or any(k in nm for k in keys) for nm in contacts):
            continue
        near = min((v for nm, v in contacts.items() if nm.startswith(keys) or any(k in nm for k in keys)), default=0.0)
        for _ in range(30):
            c.v.show(pl, colors=red, hide=hidden(pl, hide_fn), opacity=op)
            c.v.camera(*cam)
            c._emit(caption(c.v.image(), f"In the way: {title}", f"the balance first meets it {-near:.0f} mm before the dose point", TAG))
    for _ in range(48):
        c._emit(caption(c.v.image(), "The EC docks 2 mm behind the outlet and its guide and P16 stand under it: inside the breeze break's 86 mm radius",
                        "fitting the HR-100A means moving that column and opening the frame's front base rail: see README, item 6", TAG))
    c.done()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--movie", action="store_true")
    ap.add_argument("--features", nargs="?", const="all", default=None)
    ap.add_argument("--fast", action="store_true", help="half-length movie (for checking)")
    ap.add_argument("--scale-fit", action="store_true")
    ap.add_argument("--steps", nargs="?", const="all", default=None, help="v11: only the assembly-step images (renders/steps/), or e.g. --steps 8,12")
    ap.add_argument("--only", default="", help="v11: with --stills, only these stills, e.g. --only rig_iso,rig_tilt90")
    a = ap.parse_args()
    if a.scale_fit:
        scale_fit()
    elif a.movie:
        movie(a.fast)
    elif a.features:
        features("" if a.features == "all" else a.features)
    elif a.steps:
        step_images(only=() if a.steps == "all" else tuple(int(s) for s in a.steps.split(",") if s))
    else:
        stills(quick=a.quick, only=tuple(s for s in a.only.split(",") if s))


if __name__ == "__main__":
    main()
