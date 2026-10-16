#!/usr/bin/env python3
"""3D frames of the powder doser running one dose, for the slide animation:
one square PNG per output frame, one fixed camera, no text at all.

The doser is the CAD assembly of ``cad/full-assembly`` (PR #170: its parts,
colours, poses and the three-piece solenoid of ``animate.py``, so the plunger
can move).  Added here, in the same world frame (the Fusion baseplate's: Z up,
outlet towards -Y) and drawn in the June render frame like the rest:

* powder grains: Ø2.4 mm spheres let out of the Ø3 hole in the centre of the
  auger's outlet face (the face centre moved through the auger's pose at the
  frame's tilt), with a small random velocity mostly along the tube axis,
  falling under gravity (9810 mm/s², seeded, so every run is the same) into
  the cup, where they stop on the powder pile; the pile grows with every grain
  that lands (a heap that spreads to the wall, then rises), and grains that
  landed stay on its surface until the pile buries them.  Each grain of the
  timeline is drawn as --grain-mult spheres (default 4, each let out at its own
  moment in the frame), so the bulk stream reads as a continuous stream at
  slide size and the trickle as a few grains; the pile ends 10 mm deep (mean)
  whatever the count.  The grains are the same in every blur sub-frame, so
  they stay sharp;
* a clear cup (Ø45 x 50 mm, its rim 8 mm under the mounting board's
  underside) right under the stream, on the Ø90 pan of a balance (a 180 x 200
  x 70 mm rounded body with a blank display strip).

Input: a per-frame timeline (JSON)::

    {"fps": 30, "frames": [{"t": 0.0, "tilt": 0.0, "auger": [0.0], "tap": [0.0],
                            "emit": 0.0, "puff": 0, "stage": "rest"}, ...]}

    tilt   plate tilt (deg)
    auger  auger angles (deg), one per sub-frame: N > 1 sub-frames are
           rendered and averaged (motion blur of the fast-turning auger)
    tap    the solenoid plunger's share of its stroke (0 at rest, 1 on the
           tube), one per sub-frame
    emit   grains let out of the outlet during the frame (a steady stream;
           the fractional parts carry over)
    puff   grains knocked out at once by a tap in this frame
    stage  label (ignored)

The grains are simulated once, in order, before rendering; frames whose
pose, grains and pile are all the same are rendered once and copied.  Each
frame is rendered at --scale times --size and scaled down (LANCZOS).

    xvfb-run -a python3 render_procedure.py --timeline timeline.json --out-dir /tmp/procedure_frames
        [--cad-dir DIR]   # default: $FULL_ASSEMBLY_DIR, else ../../../../cad/full-assembly
                          # (from this script), else /tmp/fa/cad/full-assembly
        [--jobs 3] [--scale 2] [--size 1080]
        [--frames 0:50]   # only these output frames (A:B, or a comma list of
                          # frames and ranges); the grains are still simulated from 0
        [--grain-mult 4]  # spheres per grain of the timeline

Writes ``frame_00000.png`` ... and ``contact.png`` (12 frames spread evenly,
4 x 3) to --out-dir.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import get_context
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent

# --------------------------------------------------------------------------- #
# Camera: one for the whole animation.  Direction from the scene towards the
# camera in the June frame (outlet towards +Y, stepper on +X): mostly from the
# stepper side so the tube's tilt reads, a little from the outlet end, 20 deg up.
# --------------------------------------------------------------------------- #
CAM_DIR = (0.78, 0.50, 0.36)
CAM_MARGIN = 0.95
FIT_TILTS = (0.0, 20.0, 40.0)

# Powder (world mm, s)
GRAIN_D = 2.4
GRAIN_RGB = (0.45, 0.42, 0.38)
PILE_RGB = (0.50, 0.47, 0.42)
GRAIN_MULT = 4          # spheres drawn per grain of the timeline
GRAVITY = 9810.0
SEED = 412
FILL_MM = 10.0          # mean depth of powder in the cup once every grain is in
REPOSE = 0.50           # slope of the heap (tan of its angle of repose)

# Cup and balance (world mm).  The board's underside is at z = -38.1.
CUP_R, CUP_H, CUP_WALL, CUP_FLOOR = 22.5, 50.0, 1.2, 2.0
CUP_RIM_Z = -46.0
CUP_RGB, CUP_OPACITY = (0.84, 0.89, 0.95), 0.18
PAN_R, PAN_T, STEM_H = 45.0, 3.0, 6.0
PAN_RGB = (0.80, 0.81, 0.83)
BAL_W, BAL_D, BAL_H = 180.0, 200.0, 70.0      # x, y, z
BAL_FRONT = 115.0                              # pan centre to the body's front face (-Y)
BAL_RGB = (0.86, 0.86, 0.87)
DISPLAY_RGB = (0.16, 0.18, 0.21)

SOL = "Solenoid (Adafruit 412)"


# --------------------------------------------------------------------------- #
# CAD project
# --------------------------------------------------------------------------- #
def resolve_cad_dir(arg: str | None) -> Path:
    if arg:
        cands = [arg]
    else:
        cands = [os.environ.get("FULL_ASSEMBLY_DIR"), HERE / "../../../../cad/full-assembly",
                 "/tmp/fa/cad/full-assembly"]
    for c in cands:
        if c and (Path(c) / "assembly_bom.py").exists():
            return Path(c).resolve()
    sys.exit(f"no cad/full-assembly project (assembly_bom.py) in {[str(c) for c in cands if c]}")


def load_cad(cad_dir: Path):
    for p in (cad_dir / "onshape", cad_dir):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import animate as an
    import assembly_bom as ab
    import build
    import layout
    return an, ab, build, layout


def to_june(build, p) -> np.ndarray:
    p = np.asarray(p, float).reshape(-1, 3)
    return p @ build.W2J[:3, :3].T + build.W2J[:3, 3]


def outlet(layout, tilt: float):
    """World centre of the auger's outlet face (the Ø3 hole) and the
    outward tube axis, at a tilt (the auger's own angle doesn't move them)."""
    M = layout.placements(tilt)["Auger"][1]
    return M[:3, 3].copy(), -M[:3, 2].copy()


# --------------------------------------------------------------------------- #
# Powder: grains in flight, grains resting on the pile, the pile
# --------------------------------------------------------------------------- #
def pile_shape(vol: float, R: float):
    """(base height, cone height) of the pile for a volume (mm3) in a cup of
    inner radius R: a cone of slope REPOSE until it reaches the wall, then a
    flat-topped column under the full cone."""
    if vol <= 0:
        return None
    v_cone = math.pi * R * R * (REPOSE * R) / 3.0
    if vol <= v_cone:
        return 0.0, (3.0 * vol * REPOSE ** 2 / math.pi) ** (1.0 / 3.0)
    return (vol - v_cone) / (math.pi * R * R), REPOSE * R


def pile_height(shape, r):
    """Pile surface over the cup floor at radius r (mm)."""
    if shape is None:
        return np.zeros_like(np.asarray(r, float))
    hb, hc = shape
    return hb + np.maximum(0.0, hc - REPOSE * np.asarray(r, float))


def simulate(frames, fps, layout, cup_xy, mult=GRAIN_MULT):
    """Grains in output time, mult spheres per grain of the timeline.
    Returns one dict per frame (flying and resting grain centres, world mm;
    the pile shape), the landing points and a summary."""
    rng = np.random.default_rng(SEED)
    dt = 1.0 / fps
    cx, cy = cup_xy
    r_pile = CUP_R - CUP_WALL - 0.15
    floor = CUP_RIM_Z - CUP_H + CUP_FLOOR + 0.05
    rg = GRAIN_D / 2
    n_total = mult * (sum(int(f.get("puff", 0)) for f in frames) + int(
        math.floor(sum(float(f.get("emit", 0.0)) for f in frames) + 1e-6)))
    vol_grain = FILL_MM * math.pi * r_pile ** 2 / max(n_total, 1)
    g = np.array([0.0, 0.0, -GRAVITY])
    P0 = np.zeros((0, 3))
    V0 = np.zeros((0, 3))
    TS = np.zeros(0)
    rest = np.zeros((0, 3))
    landed, acc, missed = 0, 0.0, 0
    land_pts = []
    out = []
    for i, f in enumerate(frames):
        t = i * dt
        acc += float(f.get("emit", 0.0))
        n = int(math.floor(acc + 1e-9))
        acc -= n
        n, p = n * mult, int(f.get("puff", 0)) * mult
        if n + p:
            o, u = outlet(layout, float(f["tilt"]))
            e1 = np.cross(u, (1.0, 0.0, 0.0))
            e1 /= np.linalg.norm(e1)
            e2 = np.cross(u, e1)
            k = n + p
            ang = rng.random(k) * 2 * math.pi
            rad = 0.35 * np.sqrt(rng.random(k))           # a Ø2.4 grain in the Ø3 hole
            p0 = (o + u * (rg + 0.3) + np.outer(np.cos(ang) * rad, e1)
                  + np.outer(np.sin(ang) * rad, e2))
            speed = np.r_[rng.uniform(15.0, 40.0, n), rng.uniform(20.0, 60.0, p)]
            sig = np.r_[np.full(n, 9.0), np.full(p, 25.0)]
            v0 = u * speed[:, None] + rng.normal(0.0, 1.0, (k, 3)) * sig[:, None]
            age = np.r_[rng.random(n) * dt, rng.random(p) * 0.5 * dt]   # out during the frame
            P0, V0, TS = np.vstack([P0, p0]), np.vstack([V0, v0]), np.r_[TS, t - age]
        a = (t - TS)[:, None]
        pos = P0 + V0 * a + 0.5 * g * a * a
        shape = pile_shape(landed * vol_grain, r_pile)
        dx, dy = pos[:, 0] - cx, pos[:, 1] - cy
        r = np.hypot(dx, dy)
        surf = floor + pile_height(shape, r)
        inside = r < r_pile - rg
        below_rim = pos[:, 2] < CUP_RIM_Z
        hit = (inside & (pos[:, 2] - rg <= surf)) | (~inside & below_rim & (r < CUP_R + 1.0))
        lost = ~inside & below_rim & (r >= CUP_R + 1.0) & (pos[:, 2] < CUP_RIM_Z - CUP_H)
        if hit.any():
            s = np.minimum(1.0, (r_pile - rg) / np.maximum(r[hit], 1e-9))
            hx, hy = cx + dx[hit] * s, cy + dy[hit] * s
            hz = floor + pile_height(shape, np.hypot(hx - cx, hy - cy)) + 0.35 * GRAIN_D
            rest = np.vstack([rest, np.c_[hx, hy, hz]])
            land_pts.append(pos[hit, :2])
            landed += int(hit.sum())
        missed += int(lost.sum())
        keep = ~(hit | lost)
        P0, V0, TS, pos = P0[keep], V0[keep], TS[keep], pos[keep]
        shape = pile_shape(landed * vol_grain, r_pile)
        if len(rest):           # grains the pile has covered are gone
            rr = np.hypot(rest[:, 0] - cx, rest[:, 1] - cy)
            rest = rest[rest[:, 2] > floor + pile_height(shape, rr) + 0.1 * GRAIN_D]
        out.append(dict(flying=pos.copy(), rest=rest.copy(), pile=shape))
    land = np.vstack(land_pts) if land_pts else np.zeros((0, 2))
    info = dict(n_total=n_total, landed=landed, missed=missed, in_air=len(P0),
                fill=landed * vol_grain / (math.pi * r_pile ** 2),
                peak=float(pile_height(pile_shape(landed * vol_grain, r_pile), 0.0)))
    return out, land, info


# --------------------------------------------------------------------------- #
# Extra geometry (VTK), built in each process
# --------------------------------------------------------------------------- #
def _revolve(profile, res=96):
    """Surface of revolution about z of a polyline [(r, z), ...]."""
    import vtk
    pts = vtk.vtkPoints()
    line = vtk.vtkPolyLine()
    line.GetPointIds().SetNumberOfIds(len(profile))
    for i, (r, z) in enumerate(profile):
        pts.InsertNextPoint(float(r), 0.0, float(z))
        line.GetPointIds().SetId(i, i)
    cells = vtk.vtkCellArray()
    cells.InsertNextCell(line)
    pd = vtk.vtkPolyData()
    pd.SetPoints(pts)
    pd.SetLines(cells)
    ext = vtk.vtkRotationalExtrusionFilter()
    ext.SetInputData(pd)
    ext.SetResolution(res)
    ext.SetAngle(360.0)
    ext.CappingOff()
    tri = vtk.vtkTriangleFilter()
    tri.SetInputConnection(ext.GetOutputPort())
    nrm = vtk.vtkPolyDataNormals()
    nrm.SetInputConnection(tri.GetOutputPort())
    nrm.SetFeatureAngle(40.0)
    nrm.SplittingOn()
    nrm.Update()
    return nrm.GetOutput()


def _arc(cx, cz, r, a0, a1, n=6):
    return [(cx + r * math.cos(math.radians(a)), cz + r * math.sin(math.radians(a)))
            for a in np.linspace(a0, a1, n)]


def cup_profile():
    R, H, w, F = CUP_R, CUP_H, CUP_WALL, CUP_FLOOR
    return ([(0.0, 0.0)] + _arc(R - 1.5, 1.5, 1.5, -90, 0) + _arc(R - w / 2, H - w / 2, w / 2, 0, 180, 7)
            + _arc(R - w - 1.0, F + 1.0, 1.0, 0, -90) + [(0.0, F)])


def pan_profile():
    return ([(0.0, -PAN_T - STEM_H), (8.0, -PAN_T - STEM_H), (8.0, -PAN_T)]
            + _arc(PAN_R - 1.0, -PAN_T + 1.0, 1.0, -90, 0, 4) + _arc(PAN_R - 0.8, -0.8, 0.8, 0, 90, 4)
            + [(0.0, 0.0)])


def pile_profile(shape):
    hb, hc = shape
    rc = min(hc / REPOSE, CUP_R - CUP_WALL - 0.15)
    top = [(r, hb + hc - REPOSE * r) for r in np.linspace(0.0, rc, 12)]
    return top + ([(rc, 0.0)] if hb > 0 else [])


class Extras:
    """Cup, balance, pile and grains, added to a View's renderer."""

    def __init__(self, view, build, cup_xy, translucent=True):
        import cadquery as cq
        import vtk
        self.build, self.view = build, view
        cx, cy = cup_xy
        ren = view.ren
        bottom = CUP_RIM_Z - CUP_H

        def actor(pd, rgb, M_world, spec=0.2, power=15.0, ambient=0.0):
            m = vtk.vtkPolyDataMapper()
            m.SetInputData(pd)
            a = vtk.vtkActor()
            a.SetMapper(m)
            p = a.GetProperty()
            p.SetColor(*rgb)
            p.SetSpecular(spec)
            p.SetSpecularPower(power)
            if ambient:          # lit from the camera only, faces up would go dark
                p.SetAmbient(ambient)
                p.SetDiffuse(1.0 - 0.6 * ambient)
            a.SetUserTransform(build._vtk_matrix(build.W2J @ M_world))
            ren.AddActor(a)
            return a

        def T(x, y, z):
            M = np.eye(4)
            M[:3, 3] = (x, y, z)
            return M

        # balance: rounded body, display strip on the front (-Y), pan on a stem
        z_body = bottom - PAN_T - STEM_H
        body = (cq.Workplane("XY").box(BAL_W, BAL_D, BAL_H).edges("|Z").fillet(12.0)
                .faces(">Z").edges().fillet(4.0))
        yb = cy - BAL_FRONT + BAL_D / 2
        actor(build._polydata(body.val()), BAL_RGB, T(cx, yb, z_body - BAL_H / 2), spec=0.15, ambient=0.45)
        disp = cq.Workplane("XY").box(76.0, 2.0, 18.0).edges("|Y").fillet(1.5)
        actor(build._polydata(disp.val()), DISPLAY_RGB,
              T(cx, cy - BAL_FRONT - 0.6, z_body - 20.0), spec=0.5, power=40.0)
        for sx in (-1, 1):
            btn = cq.Workplane("XZ").circle(4.0).extrude(1.6)
            actor(build._polydata(btn.val()), (0.55, 0.57, 0.60),
                  T(cx + sx * 56.0, cy - BAL_FRONT, z_body - 20.0), spec=0.3)
        actor(_revolve(pan_profile()), PAN_RGB, T(cx, cy, bottom), spec=0.5, power=30.0, ambient=0.4)
        # the cup: clear plastic (depth peeling for the see-through walls)
        self.cup = actor(_revolve(cup_profile()), CUP_RGB, T(cx, cy, bottom), spec=0.6, power=50.0)
        if translucent:
            self.cup.GetProperty().SetOpacity(CUP_OPACITY)
            view.win.SetAlphaBitPlanes(1)
            view.win.SetMultiSamples(0)
            ren.SetUseDepthPeeling(1)
            ren.SetMaximumNumberOfPeels(8)
            ren.SetOcclusionRatio(0.0)
        # the pile (rebuilt per frame) and the grains (glyphs on points, June frame)
        self.M_pile = T(cx, cy, bottom + CUP_FLOOR + 0.05)
        self.pile = vtk.vtkActor()
        self.pile_mapper = vtk.vtkPolyDataMapper()
        self.pile.SetMapper(self.pile_mapper)
        self.pile.GetProperty().SetColor(*PILE_RGB)
        self.pile.GetProperty().SetAmbient(0.2)
        self.pile.GetProperty().SetDiffuse(0.85)
        self.pile.GetProperty().SetSpecular(0.05)
        self.pile.SetUserTransform(build._vtk_matrix(build.W2J @ self.M_pile))
        ren.AddActor(self.pile)
        sph = vtk.vtkSphereSource()
        sph.SetRadius(GRAIN_D / 2)
        sph.SetThetaResolution(12)
        sph.SetPhiResolution(8)
        self.grain_pts = vtk.vtkPoints()
        self.grain_pd = vtk.vtkPolyData()
        self.grain_pd.SetPoints(self.grain_pts)
        gm = vtk.vtkGlyph3DMapper()
        gm.SetInputData(self.grain_pd)
        gm.SetSourceConnection(sph.GetOutputPort())
        gm.ScalingOff()
        self.grains = vtk.vtkActor()
        self.grains.SetMapper(gm)
        self.grains.GetProperty().SetColor(*GRAIN_RGB)
        self.grains.GetProperty().SetAmbient(0.12)
        self.grains.GetProperty().SetSpecular(0.2)
        self.grains.GetProperty().SetSpecularPower(20.0)
        ren.AddActor(self.grains)
        self._pile_key = None

    def set_powder(self, grains_june: np.ndarray, pile):
        from vtkmodules.util.numpy_support import numpy_to_vtk
        g = np.ascontiguousarray(np.asarray(grains_june, float).reshape(-1, 3))
        self.grain_pts.SetData(numpy_to_vtk(g, deep=True))
        self.grain_pts.Modified()
        self.grain_pd.Modified()
        self.grains.SetVisibility(len(g) > 0)
        if pile is None:
            self.pile.SetVisibility(False)
            return
        key = tuple(np.round(pile, 4))
        if key != self._pile_key:
            self.pile_mapper.SetInputData(_revolve(pile_profile(pile), res=72))
            self._pile_key = key
        self.pile.SetVisibility(True)


# --------------------------------------------------------------------------- #
# Rendering, in worker processes (each with its own scene and window)
# --------------------------------------------------------------------------- #
_W = {}


def _init_worker(cad_dir, render_px, cam, cup_xy, board, size):
    os.environ.setdefault("LP_NUM_THREADS", "2")
    an, ab, build, layout = load_cad(Path(cad_dir))
    order, inst = ab.scene()
    view = ab.View(order, inst, (render_px, render_px))
    sol = an.solenoid_actors(view)
    for a in sol.values():
        a.SetVisibility(True)
    extras = Extras(view, build, cup_xy)
    c = view.ren.GetActiveCamera()
    c.SetPosition(*cam[0])
    c.SetFocalPoint(*cam[1])
    c.SetViewAngle(float(cam[2]))
    c.SetViewUp(0, 0, 1)
    _W.update(an=an, ab=ab, view=view, sol=sol, extras=extras, board=board, size=size)


def _render(job):
    path, spec = job
    t0 = time.time()
    an, ab, view, sol = _W["an"], _W["ab"], _W["view"], _W["sol"]
    _W["extras"].set_powder(spec["grains"], spec["pile"])
    acc = None
    for a_deg, s in zip(spec["auger"], spec["tap"]):
        P = ab.poses(spec["tilt"], a_deg)
        view.pose(lambda kk: 1.0, tilt_M=P)
        view.actors[SOL].SetVisibility(False)
        view.actors["Mounting board"].SetVisibility(_W["board"])
        an.tap_pose(sol, P[SOL], float(s) * an.STROKE)
        view.ren.ResetCameraClippingRange()
        img = np.asarray(view.image(), dtype=np.float32)
        acc = img if acc is None else acc + img
    img = Image.fromarray(np.clip(acc / len(spec["auger"]) + 0.5, 0, 255).astype(np.uint8))
    size = _W["size"]
    if img.size != (size, size):
        img = img.resize((size, size), Image.LANCZOS)
    img.save(path, compress_level=3)
    return path, time.time() - t0, len(spec["auger"])


def contact_sheet(paths, out, cols=4, rows=3, w=270) -> None:
    sheet = Image.new("RGB", (w * cols + 4 * (cols - 1), w * rows + 4 * (rows - 1)), (200, 200, 200))
    for i, p in enumerate(paths[:cols * rows]):
        sheet.paste(Image.open(p).convert("RGB").resize((w, w), Image.LANCZOS),
                    ((i % cols) * (w + 4), (i // cols) * (w + 4)))
    sheet.save(out)


def parse_frames(spec: str | None, n: int) -> list[int]:
    if not spec:
        return list(range(n))
    out = []
    for part in spec.split(","):
        if ":" in part:
            a, b = part.split(":")
            out += range(int(a or 0), min(int(b) if b else n, n))
        else:
            out.append(int(part))
    return sorted({i for i in out if 0 <= i < n})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cad-dir", help="cad/full-assembly of PR #170")
    ap.add_argument("--timeline", default=str(HERE / "timeline.json"))
    ap.add_argument("--out-dir", default="/tmp/procedure_frames")
    ap.add_argument("--jobs", type=int, default=3, help="render processes")
    ap.add_argument("--scale", type=int, default=2, help="render at this many times the size, then scale down")
    ap.add_argument("--size", type=int, default=1080, help="output frame size (px, square)")
    ap.add_argument("--frames", help="only these output frames: A:B, or a comma list of frames and A:B ranges")
    ap.add_argument("--camera-dir", help="override the camera direction (June frame x,y,z)")
    ap.add_argument("--no-board", action="store_true", help="leave the mounting board out")
    ap.add_argument("--grain-mult", type=int, default=GRAIN_MULT,
                    help="spheres drawn per grain of the timeline (stream density)")
    args = ap.parse_args()
    t_start = time.time()

    cad_dir = resolve_cad_dir(args.cad_dir)
    an, ab, build, layout = load_cad(cad_dir)
    tl = json.loads(Path(args.timeline).read_text())
    frames, fps = tl["frames"], float(tl.get("fps", 30))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # the grains: once with the cup under the outlet at tilt 0, then again with
    # the cup centred on where they landed
    o0, _ = outlet(layout, 0.0)
    _, land, _ = simulate(frames, fps, layout, (o0[0], o0[1]), args.grain_mult)
    cup_xy = (float(o0[0]), float(np.mean(land[:, 1]))) if len(land) else (float(o0[0]), float(o0[1]))
    sim, land, info = simulate(frames, fps, layout, cup_xy, args.grain_mult)
    for t in (0.0, 10.0, 15.0, 40.0):
        o, u = outlet(layout, t)
        print(f"  outlet at tilt {t:4.1f}: world {np.round(o, 2)}, June {np.round(to_june(build, o)[0], 2)}, "
              f"axis out {np.round(u, 3)}")
    print(f"  cup centre (world) x {cup_xy[0]:.2f}, y {cup_xy[1]:.2f}; rim z {CUP_RIM_Z} "
          f"(board underside {-layout.BOARD_T})")
    if len(land):
        d = np.hypot(land[:, 0] - cup_xy[0], land[:, 1] - cup_xy[1])
        print(f"  landing points: max {d.max():.1f} mm from the cup axis (inner radius {CUP_R - CUP_WALL})")
    print(f"  grains: {info['n_total']} out, {info['landed']} landed, {info['missed']} missed the cup, "
          f"{info['in_air']} still falling; pile {info['fill']:.1f} mm mean, {info['peak']:.1f} mm peak")

    # the fixed camera: the doser at 0-40 deg, the stream, the cup, the pan and
    # the top of the balance
    order, inst = ab.scene()
    view = ab.View(order, inst, (args.size, args.size))
    one = lambda kk: 1.0       # noqa: E731
    sel = [d for d in order if d["name"] != "Mounting board"]       # the board may run out of the frame
    pts = [ab._points(sel, inst, one, tilt_M=ab.poses(t), every=7) for t in FIT_TILTS]
    bottom = CUP_RIM_Z - CUP_H
    z_body = bottom - PAN_T - STEM_H
    yb0 = cup_xy[1] - BAL_FRONT
    pts.append(an.box((cup_xy[0] - PAN_R, cup_xy[1] - PAN_R, bottom - PAN_T),
                      (cup_xy[0] + PAN_R, cup_xy[1] + PAN_R, CUP_RIM_Z)))
    pts.append(an.box((cup_xy[0] - PAN_R, yb0, z_body - 8.0), (cup_xy[0] + PAN_R, cup_xy[1], z_body)))
    fl = [s["flying"] for s in sim if len(s["flying"])]
    if fl:
        pts.append(np.vstack(fl)[::5])
    dirv = tuple(float(v) for v in args.camera_dir.split(",")) if args.camera_dir else CAM_DIR
    cam = an.fit_camera(view, np.vstack(pts), dirv, margin=CAM_MARGIN, band=(0, 0))
    cam = tuple(np.asarray(c, float).tolist() for c in cam)
    print(f"  camera (June frame): direction {np.round(np.asarray(dirv) / np.linalg.norm(dirv), 3)}, "
          f"position {np.round(cam[0], 1)}, focal point {np.round(cam[1], 1)}, view angle {cam[2]:.2f} deg")
    del view

    # one spec per output frame; identical ones are rendered once
    picks = parse_frames(args.frames, len(frames))
    specs, keys = {}, {}
    for i in picks:
        f, s = frames[i], sim[i]
        g = np.vstack([s["flying"], s["rest"]])
        spec = dict(tilt=float(f["tilt"]), auger=[float(a) for a in f["auger"]],
                    tap=[float(x) for x in f["tap"]], grains=to_june(build, g).astype(np.float32),
                    pile=None if s["pile"] is None else tuple(float(v) for v in s["pile"]))
        assert len(spec["auger"]) == len(spec["tap"]), i
        h = hashlib.sha1(json.dumps([round(spec["tilt"], 6), [round(a, 6) for a in spec["auger"]],
                                     [round(x, 6) for x in spec["tap"]],
                                     None if spec["pile"] is None else [round(v, 5) for v in spec["pile"]]]
                                    ).encode())
        h.update(np.round(spec["grains"], 3).tobytes())
        keys[i] = h.hexdigest()
        specs.setdefault(keys[i], (i, spec))
    jobs = [(str(out_dir / f"frame_{i:05d}.png"), spec) for i, spec in specs.values()]
    n_sub = sum(len(s["auger"]) for _, s in jobs)
    print(f"  {len(picks)} frames ({len(frames)} in the timeline, {len(frames) / fps:.1f} s), "
          f"{len(jobs)} to render, {n_sub} sub-frames at {args.size * args.scale} px; "
          f"setup {time.time() - t_start:.0f} s", flush=True)

    t_render = time.time()
    done = 0
    with ProcessPoolExecutor(args.jobs, mp_context=get_context("spawn"), initializer=_init_worker,
                             initargs=(str(cad_dir), args.size * args.scale, cam, cup_xy,
                                       not args.no_board, args.size)) as ex:
        futs = [ex.submit(_render, j) for j in sorted(jobs, key=lambda j: -len(j[1]["auger"]))]
        for fu in as_completed(futs):
            fu.result()
            done += 1
            if done % 50 == 0 or done == len(jobs):
                el = time.time() - t_render
                print(f"  rendered {done}/{len(jobs)}  ({el:.0f} s)", flush=True)
    first = {k: i for k, (i, _) in specs.items()}
    for i in picks:
        if first[keys[i]] != i:
            shutil.copyfile(out_dir / f"frame_{first[keys[i]]:05d}.png", out_dir / f"frame_{i:05d}.png")
    paths = [out_dir / f"frame_{i:05d}.png" for i in picks]
    sel = [paths[j] for j in np.linspace(0, len(paths) - 1, min(12, len(paths))).astype(int)]
    contact_sheet(sel, out_dir / "contact.png")
    print(f"  -> {out_dir}/frame_*.png ({len(picks)} frames, {args.size}x{args.size}), contact.png; "
          f"render {time.time() - t_render:.0f} s, total {time.time() - t_start:.0f} s")


if __name__ == "__main__":
    main()
