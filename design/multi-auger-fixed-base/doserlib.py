"""Shared geometry for the fixed-base multi-auger concepts (issue #204).

One "unit" is the current doser module from PR #170 (the parts in #193's
Onshape documents): mounting plate, auger + cap, two brackets, tap collar
on its base, Adafruit 412 solenoid, NEMA 11 + 20T pinion, and, depending
on the drive variant, the 28T tilt gears, 14T servo pinions and MG996R
servos.  The STEP files and PR #170's ``layout.py`` are read at a pinned
commit of PR #170's branch, so nothing here is re-modelled by eye.

Unit frame (used by every concept): the hinge axis is the X axis through
the origin, the outlet points to -Y (11.6 mm in front of the hinge at
tilt 0), Z is up.  PR #170's world frame is this one shifted by
(0, 45.4, 43.25).  Tilt is about +X, positive = rear up / outlet down.

Station frame: Z up, the beaker axis is the Z axis.  ``place(theta, R, h)``
puts a unit's hinge at radius R and bearing theta (deg) from the beaker
axis, outlet pointing at the axis, hinge at height h.
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

PR170_SHA = "7f5b3b779e1d036f001c0cbf9f979721139b904d"   # PR #170 head, 17 Oct 2026
RAW = f"https://raw.githubusercontent.com/vertical-cloud-lab/powder-doser/{PR170_SHA}/cad/full-assembly"
CACHE = Path(os.environ.get("PR170_CACHE", Path.home() / ".cache" / "powder-doser-pr170" / PR170_SHA))

STEP_FILES = [
    "components/fusion-step/mounting-plate.step",
    "components/fusion-step/baseplate.step",
    "components/fusion-step/auger.step",
    "components/fusion-step/auger-cap.step",
    "components/fusion-step/brackets.step",
    "components/fusion-step/tap-collar.step",
    "components/fusion-step/servo-pinion.step",
    "components/fusion-step/stepper-pinion.step",
    "components/ai-step/tap-collar-base.step",
    "components/purchased/adafruit-412-solenoid.step",
    "components/purchased/mg996r-servo.step",
    "components/purchased/nema11-11hs18-0674s.step",
    "onshape/layout.py",
]


def fetch_pr170() -> Path:
    """Download PR #170's parts and layout.py once (pinned commit)."""
    for rel in STEP_FILES:
        dst = CACHE / rel
        if dst.exists() and dst.stat().st_size > 0:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        print(f"  fetching {rel}")
        urllib.request.urlretrieve(f"{RAW}/{rel}", dst)
    return CACHE


def load_layout():
    root = fetch_pr170()
    spec = importlib.util.spec_from_file_location("pr170_layout", root / "onshape" / "layout.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["pr170_layout"] = mod
    spec.loader.exec_module(mod)
    mod.COMP = root / "components"
    return mod


L = load_layout()
import cadquery as cq  # noqa: E402  (after the layout so its import order matches PR #170)

HINGE = np.array([0.0, L.HINGE_Y, L.HINGE_Z])
W2U = np.eye(4)
W2U[:3, 3] = -HINGE                         # PR #170 world -> unit frame
OUTLET_AHEAD = 11.6                          # outlet ahead of the hinge, tilt 0 (PR #170)
BASE_TOP_U = 6.0 - L.HINGE_Z                 # baseplate top in the unit frame (-37.25)
BASE_BOT_U = -L.HINGE_Z                      # baseplate underside (-43.25)


# --------------------------------------------------------------------------- #
# small transforms
# --------------------------------------------------------------------------- #
def Tt(x=0.0, y=0.0, z=0.0) -> np.ndarray:
    M = np.eye(4)
    M[:3, 3] = (x, y, z)
    return M


def Rz(deg) -> np.ndarray:
    return L.rot_about((0, 0, 1), deg)


def Rx(deg) -> np.ndarray:
    return L.rot_about((1, 0, 0), deg)


def place(theta_deg: float, R: float, h: float) -> np.ndarray:
    """Unit frame -> station frame: hinge at bearing theta, radius R, height h;
    the unit's +Y (its rear) points away from the beaker axis."""
    return Tt(R * math.cos(math.radians(theta_deg)), R * math.sin(math.radians(theta_deg)), h) @ Rz(theta_deg - 90.0)


def outlet_point(tilt_deg: float) -> np.ndarray:
    t = math.radians(tilt_deg)
    return np.array([0.0, -OUTLET_AHEAD * math.cos(t), -OUTLET_AHEAD * math.sin(t)])


# --------------------------------------------------------------------------- #
# shapes
# --------------------------------------------------------------------------- #
_SHAPES: dict = {}


def step_shape(rel: str):
    if rel not in _SHAPES:
        _SHAPES[rel] = L._shape(L.COMP / rel)
    return _SHAPES[rel]


def mp_bodies() -> dict:
    """The mounting plate's five STEP bodies, in its own (MP) frame.  MP Z is
    the hinge axis; world x = -MPz - 41.8, so the MP z 0..12.3 bodies are the
    -X gear and its web, the MP z -95.9..-83.6 ones the +X gear and web."""
    if "mp" not in _SHAPES:
        sols = cq.importers.importStep(str(L.COMP / "fusion-step/mounting-plate.step")).vals()[0].Solids()
        out = {}
        for s in sols:
            bb, v = s.BoundingBox(), s.Volume()
            side = "-X" if bb.zmin > -1.0 else ("+X" if bb.zmax < -80.0 else None)
            if side is None:
                out["plate"] = s
            elif v > 5000:
                out["gear" + side] = s
            else:
                out["web" + side] = s
        _SHAPES["mp"] = out
    return _SHAPES["mp"]


def sector_gear(gear, a0=150.0, a1=300.0, hub_r=11.0):
    """Keep the gear teeth between MP-frame angles a0..a1 (measured from MP +X,
    the outlet direction, towards MP +Y, up), plus a hub.  With the servo
    pinion behind the hinge (MP -X = 180 deg), the teeth that ever mesh over
    0..90 deg of tilt lie between 180 and 270 deg at tilt 0."""
    bb = gear.BoundingBox()
    r = 40.0
    pts = [(0.0, 0.0)] + [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
                          for a in np.linspace(a0, a1, 16)]
    wedge = (cq.Workplane("XY").workplane(offset=bb.zmin - 1).polyline(pts).close()
             .extrude(bb.zlen + 2).val())
    hub = cq.Solid.makeCylinder(hub_r, bb.zlen + 2, cq.Vector(0, 0, bb.zmin - 1))
    return gear.intersect(wedge.fuse(hub))


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def cyl(r, h, x=0.0, y=0.0, z=0.0, d=(0, 0, 1)):
    return cq.Solid.makeCylinder(r, h, cq.Vector(x, y, z), cq.Vector(*d))


def tower(x_in, x_out, front=-9.0, back=28.0):
    """A hinge tower like the baseplate's (|x| 28.9..41.2, 9 mm ahead of the
    hinge, 9 mm above it, rounded top), standing on the base top, with the
    M5 hole on the hinge axis."""
    xa, xb = min(x_in, x_out), max(x_in, x_out)
    t = box(xa, xb, front, back, BASE_TOP_U, 0.0)
    top = cq.Solid.makeCylinder(9.0, xb - xa, cq.Vector(xa, 0, 0), cq.Vector(1, 0, 0))
    t = t.fuse(top)
    return t.cut(cyl(2.65, xb - xa + 2, xa - 1, 0, 0, d=(1, 0, 0)))


# --------------------------------------------------------------------------- #
# the unit
# --------------------------------------------------------------------------- #
COL = {
    "plate": (0.80, 0.82, 0.86), "base": (0.62, 0.66, 0.72), "auger": (0.90, 0.76, 0.45),
    "cap": (0.30, 0.45, 0.80), "bracket": (0.55, 0.72, 0.85), "collar": (0.70, 0.45, 0.85),
    "collar_base": (0.55, 0.40, 0.70), "pinion": (0.45, 0.70, 0.55), "motor": (0.30, 0.30, 0.35),
    "servo": (0.20, 0.20, 0.22), "solenoid": (0.60, 0.62, 0.66), "gear": (0.86, 0.86, 0.88),
    "actuator": (0.25, 0.27, 0.30), "rod": (0.80, 0.81, 0.84), "glass": (0.70, 0.85, 0.95),
    "balance": (0.88, 0.88, 0.86), "new": (0.95, 0.62, 0.30), "link": (0.95, 0.62, 0.30),
    "hit": (0.90, 0.15, 0.15),
}


@dataclass
class Part:
    name: str
    shape: object                 # cq.Shape in its own frame
    M: np.ndarray                 # own frame -> station frame
    colour: tuple
    unit: str = "fixed"           # which unit it belongs to ("fixed" = base, beaker, ...)
    moving: bool = False
    opacity: float = 1.0


SERVO_TOP_X = L.SERVO_POST_INNER_X - L.SERVO_FLANGE_UNDERSIDE_BELOW_TOP   # 56.6
SPLINE_R = L.HINGE_Z - L.SERVO_SPLINE_Z                                  # 27.25 (servo pinion centre to hinge)


@dataclass
class UnitSpec:
    """drive:
    'dual-below'   the current doser: 28T gears both sides, MG996R + 14T pinion under the hinge
    'dual-flip'    as the current doser, but each servo turned end for end about its spline so its
                   case points back (the pinion, gears and plate don't change)
    'single-below' one gear + one servo, on the unit's +X side only (the -X knuckle is plain)
    'rear'         both gears; the servos moved behind the hinge (pinion 27.25 mm behind it), case pointing back
    'rear-sector'  as 'rear' with the gears cut to the sector that meshes over 0..90 deg
    'none'         no gears, no servos (tilt from a linear actuator)"""
    drive: str = "dual-below"
    collar_roll: float = L.COLLAR_ROLL_DEG
    baseplate: bool = False           # the current Fusion baseplate (problem figure only)


def unit_parts(spec: UnitSpec, tilt: float, Mst: np.ndarray, tag: str) -> list[Part]:
    """Every part of one unit at ``tilt``, placed by ``Mst`` (unit -> station)."""
    U = Mst @ W2U
    pl = L.placements(tilt, roll_deg=spec.collar_roll)
    parts: list[Part] = []

    def add(name, shape, M, colour, moving=True):
        parts.append(Part(f"{tag}:{name}", shape, M, colour, tag, moving))

    names = {
        "Auger": "auger", "Auger cap": "cap", "Bracket (rear)": "bracket", "Bracket (front)": "bracket",
        "Tap collar base (AI)": "collar_base", "Tap collar": "collar", "Solenoid (Adafruit 412)": "solenoid",
        "Stepper pinion": "pinion", "Stepper (NEMA 11)": "motor",
    }
    for n, c in names.items():
        rel, M = pl[n]
        add(n, step_shape(rel), U @ M, COL[c])
    # mounting plate, by body
    Mmp = U @ pl["Mounting plate"][1]
    b = mp_bodies()
    add("Mounting plate", b["plate"], Mmp, COL["plate"])
    sides = {"dual-below": ("+X", "-X"), "dual-flip": ("+X", "-X"), "single-below": ("+X",), "rear": ("+X", "-X"),
             "rear-sector": ("+X", "-X"), "none": ()}[spec.drive]
    for s in sides:
        g = b["gear" + s]
        if spec.drive == "rear-sector":
            g = sector_gear(g)
        add(f"28T gear {s}", g, Mmp, COL["gear"])
        add(f"gear web {s}", b["web" + s], Mmp, COL["plate"])
    # servos + pinions (fixed to the base)
    sp = L.SERVO_RATIO * tilt
    for s in sides:
        sx = 1.0 if s == "+X" else -1.0
        if spec.drive in ("dual-below", "single-below"):
            Ms = L.SERVO_POS if sx > 0 else L.SERVO_NEG
            Mp = (L.SPINION_POS @ Rz(-sp)) if sx > 0 else (L.SPINION_NEG @ Rz(sp))
        elif spec.drive == "dual-flip":   # same spline, case towards +Y (back)
            Ms = (L.T([L.Y, L.NZ, L.NX], (SERVO_TOP_X, L.HINGE_Y, L.SERVO_SPLINE_Z)) if sx > 0
                  else L.T([L.Y, L.Z, L.X], (-SERVO_TOP_X, L.HINGE_Y, L.SERVO_SPLINE_Z)))
            Mp = (L.SPINION_POS @ Rz(-sp)) if sx > 0 else (L.SPINION_NEG @ Rz(sp))
        else:   # behind the hinge at hinge height, case towards +Y (back)
            yy, zz = L.HINGE_Y + SPLINE_R, L.HINGE_Z
            if sx > 0:
                Ms = L.T([L.Y, L.NZ, L.NX], (SERVO_TOP_X, yy, zz))
                Mp = L.T([L.Y, L.Z, L.X], (L.GEAR_PLANE_X[0], yy, zz)) @ Rz(-sp)
            else:
                Ms = L.T([L.Y, L.Z, L.X], (-SERVO_TOP_X, yy, zz))
                Mp = L.T([L.Y, L.NZ, L.NX], (-L.GEAR_PLANE_X[0], yy, zz)) @ Rz(sp)
        parts.append(Part(f"{tag}:MG996R {s}", step_shape("purchased/mg996r-servo.step"), U @ Ms, COL["servo"], tag, False))
        parts.append(Part(f"{tag}:servo pinion {s}", step_shape("fusion-step/servo-pinion.step"), U @ Mp, COL["pinion"], tag, False))
    if spec.baseplate:
        parts.append(Part(f"{tag}:Baseplate", step_shape("fusion-step/baseplate.step"), U, COL["base"], tag, False))
    return parts


# --------------------------------------------------------------------------- #
# purchased / new parts
# --------------------------------------------------------------------------- #
# Actuonix P16-150-22-12-P (PR #202's pick): 150 mm stroke, 197 mm hole to
# hole closed, body about 20 x 36 mm, 50 N.  Envelope only.
P16 = dict(stroke=150.0, closed=197.0, body_w=20.0, body_d=36.0)


def p16_parts(Bp: np.ndarray, Pp: np.ndarray, tag: str, axis_x=(1.0, 0.0, 0.0)) -> list[Part]:
    """An Actuonix P16 envelope between base pin Bp and rod pin Pp (station
    frame), pin axes along ``axis_x``.  Raises if the length is outside the stroke."""
    L_ = float(np.linalg.norm(Pp - Bp))
    ext = L_ - P16["closed"]
    if ext < -0.5 or ext > P16["stroke"] + 0.5:
        raise ValueError(f"P16 length {L_:.1f} outside {P16['closed']}..{P16['closed'] + P16['stroke']}")
    w = (Pp - Bp) / L_
    ax = np.asarray(axis_x, float)
    ax = ax - w * (ax @ w)
    ax /= np.linalg.norm(ax)
    v = np.cross(w, ax)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = ax, v, w, Bp
    body_len = P16["closed"] - 30.0
    body = box(-P16["body_w"] / 2, P16["body_w"] / 2, -P16["body_d"] / 2 + 8, P16["body_d"] / 2 - 8, 8.0, 8.0 + body_len * 0.35)
    tube = box(-9.0, 9.0, -9.0, 9.0, 8.0, body_len)
    motor = box(-P16["body_w"] / 2, P16["body_w"] / 2, -P16["body_d"] / 2, 0.0, 8.0, 8.0 + body_len * 0.35)
    eye = cyl(4.5, 8.0, -4.0, 0, 0, d=(1, 0, 0)).fuse(box(-4, 4, -4.5, 4.5, 0, 9))
    shell = body.fuse(tube).fuse(motor).fuse(eye)
    rod = cyl(3.0, L_ - body_len - 6.0, 0, 0, body_len).fuse(cyl(4.0, 8.0, -4.0, 0, L_, d=(1, 0, 0))).fuse(box(-3, 3, -4, 4, L_ - 8, L_))
    return [Part(f"{tag}:P16 body", shell, M, COL["actuator"], tag, False),
            Part(f"{tag}:P16 rod", rod, M, COL["rod"], tag, True)]


def clevis_bracket(a: float, c: float):
    """Bracket under the mounting-plate floor (unit frame at tilt 0, MOVES
    with the plate): two cheeks around the rod-end pin at (y, z) = (a, -c)."""
    floor_u = 8.0 - L.HINGE_Z            # floor underside, -35.25
    cheek = lambda x0: box(x0, x0 + 3.0, a - 8, a + 8, -c - 6, floor_u)   # noqa: E731
    top = box(-8.0, 8.0, a - 12, a + 12, floor_u - 3.0, floor_u)
    return cheek(-7.0).fuse(cheek(4.0)).fuse(top).cut(cyl(2.1, 20, -10, a, -c, d=(1, 0, 0)))


def beaker(d=50.0, h=70.0):
    """ISO 3819 low-form beaker (100 mL: 50 x 70), base at z = 0."""
    return cyl(d / 2, h).cut(cyl(d / 2 - 1.5, h, 0, 0, 1.5))


def hr100a():
    """A&D HR-100A from the numbers PR #185 (v3 parts3.py) took from A&D's
    manual: base 198 x 253 (pan 95 mm from the front), pan dia 90 at 86.5,
    round breeze break 156 inside, 315 overall, top door opening dia 76.
    Bench at z = 0, pan centre on the Z axis, display towards -Y."""
    front = -95.0
    base = box(-99, 99, front, front + 253, 6, 80)
    ring = cyl(86, 6, 0, 0, 80).cut(cyl(78, 8, 0, 0, 79))
    lid = cyl(86, 315 - 284.5, 0, 0, 284.5).cut(cyl(38, 40, 0, 0, 280))
    pan = cyl(45, 2, 0, 0, 84.5).fuse(cyl(4, 6.5, 0, 0, 78))
    glass = cyl(81, 284.5 - 86, 0, 0, 86).cut(cyl(78, 200, 0, 0, 85))
    return base.fuse(ring).fuse(lid).fuse(pan), glass


# --------------------------------------------------------------------------- #
# meshes, clearance, rendering
# --------------------------------------------------------------------------- #
_MESH: dict = {}


def mesh_of(shape, tol=0.15):
    import trimesh
    k = id(shape)
    if k not in _MESH:
        v, f = shape.tessellate(tol, 0.3)
        _MESH[k] = (shape, trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in v]), np.array(f), process=False))
    return _MESH[k][1]


_BVH: dict = {}


def _bvh(shape):
    import fcl
    k = id(shape)
    if k not in _BVH:
        m = mesh_of(shape)
        b = fcl.BVHModel()
        b.beginModel(len(m.vertices), len(m.faces))
        b.addSubModel(np.asarray(m.vertices, float), np.asarray(m.faces, np.int32))
        b.endModel()
        _BVH[k] = b
    return _BVH[k]


def clearance(parts: list[Part], groups: list[tuple[str, str]] | None = None, skip=()):
    """Minimum distance between parts of different units (or the given
    (unitA, unitB) pairs).  Returns (dist, nameA, nameB), dist < 0 if they overlap
    (then -1 * nothing measured: fcl reports 0 for touching/penetrating)."""
    import fcl
    objs = []
    for p in parts:
        if any(s in p.name for s in skip):
            continue
        objs.append((p, fcl.CollisionObject(_bvh(p.shape), fcl.Transform(p.M[:3, :3], p.M[:3, 3]))))
    best = (1e9, None, None)
    req = fcl.DistanceRequest(enable_nearest_points=False)
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            pa, oa = objs[i]
            pb, ob = objs[j]
            if pa.unit == pb.unit:
                continue
            if groups and not any({pa.unit, pb.unit} == set(g) for g in groups):
                continue
            res = fcl.DistanceResult()
            d = fcl.distance(oa, ob, req, res)
            if d < best[0]:
                best = (d, pa.name, pb.name)
    return best


def collisions(parts: list[Part], skip=()):
    """Every colliding pair of parts from different units."""
    import fcl
    objs = []
    for p in parts:
        if any(s in p.name for s in skip):
            continue
        objs.append((p, fcl.CollisionObject(_bvh(p.shape), fcl.Transform(p.M[:3, :3], p.M[:3, 3]))))
    hits = []
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            pa, oa = objs[i]
            pb, ob = objs[j]
            if pa.unit == pb.unit:
                continue
            req, res = fcl.CollisionRequest(), fcl.CollisionResult()
            if fcl.collide(oa, ob, req, res):
                hits.append((pa.name, pb.name))
    return hits


def render(parts: list[Part], out: Path, view="iso", size=(1400, 1000), az=35.0, el=28.0,
           dist=1.0, focal=(0, 0, 0), highlight=(), parallel=False, extra_actors=()):
    import vtk
    from vtkmodules.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
    ren = vtk.vtkRenderer()
    ren.SetBackground(1.0, 1.0, 1.0)
    for p in parts:
        m = mesh_of(p.shape)
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
        mp = vtk.vtkPolyDataMapper()
        mp.SetInputData(nrm.GetOutput())
        a = vtk.vtkActor()
        a.SetMapper(mp)
        pr = a.GetProperty()
        pr.SetColor(*(COL["hit"] if p.name in highlight else p.colour))
        pr.SetOpacity(p.opacity)
        pr.SetAmbient(0.28)
        pr.SetDiffuse(0.78)
        pr.SetSpecular(0.18)
        pr.SetSpecularPower(15)
        t = vtk.vtkTransform()
        t.SetMatrix([float(v) for v in p.M.reshape(-1)])
        a.SetUserTransform(t)
        ren.AddActor(a)
    for a in extra_actors:
        ren.AddActor(a)
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(*focal)
    if view == "top":
        cam.SetPosition(focal[0], focal[1], focal[2] + 1000)
        cam.SetViewUp(0, 1, 0)
    elif view == "side":
        cam.SetPosition(focal[0] + 1000, focal[1], focal[2])
        cam.SetViewUp(0, 0, 1)
    elif view == "front":
        cam.SetPosition(focal[0], focal[1] - 1000, focal[2])
        cam.SetViewUp(0, 0, 1)
    else:
        a_, e_ = math.radians(az), math.radians(el)
        cam.SetPosition(focal[0] + 1000 * math.cos(e_) * math.cos(a_), focal[1] + 1000 * math.cos(e_) * math.sin(a_),
                        focal[2] + 1000 * math.sin(e_))
        cam.SetViewUp(0, 0, 1)
    if parallel:
        cam.ParallelProjectionOn()
    ren.ResetCamera()
    if dist is not None:
        if parallel:
            cam.SetParallelScale(dist)
        else:
            cam.Dolly(dist)
    ren.ResetCameraClippingRange()
    key = vtk.vtkLight()
    key.SetLightTypeToCameraLight()
    key.SetPosition(0.4, 0.6, 1.0)
    key.SetIntensity(0.85)
    ren.AddLight(key)
    fill = vtk.vtkLight()
    fill.SetLightTypeToCameraLight()
    fill.SetPosition(-0.6, -0.2, 0.8)
    fill.SetIntensity(0.35)
    ren.AddLight(fill)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(*size)
    win.AddRenderer(ren)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.ReadFrontBufferOff()
    w2i.Update()
    w = vtk.vtkPNGWriter()
    w.SetFileName(str(out))
    w.SetInputConnection(w2i.GetOutputPort())
    w.Write()
    return ren, win
