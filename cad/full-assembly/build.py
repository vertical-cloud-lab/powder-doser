"""Full powder-doser assembly (current design), rendered from the same
camera as the annotated overview render (issue #165).  PR #97 uses
``renders/assembly_iso_az090_hires_annotated_white.png`` as Fig. 1a.

Every part is a real file: the eight lab Fusion 360 designs
(``components/fusion-step/``), the AI tap-collar base the rig still uses
(``components/ai-step/``), simplified models of the purchased stepper,
servos and solenoid (``components/purchased/``), and the 46 fasteners
(``hardware.py``).  Positions come from ``onshape/layout.py`` (the same
transforms the Onshape assembly is built from) and ``hardware.py``.

The camera is the June ``render_assembly_view('iso', azimuth_deg=90)``
pinned after its ResetCamera(), so the view matches the June figure (and
the previous version of this one).  The June frame has the hinge axis
along X through (y, z) = (Y_DISP, Z_AUG) and the outlet towards +Y; the
layout's world frame (the Fusion baseplate's) has the outlet towards -Y,
so ``W2J`` turns it 180° about Z and puts the hinge axis where June had
it.  (The current outlet is 11.6 mm in front of the hinge; in June the
hinge passed through the outlet.)

Run headless from this directory::

    xvfb-run -a python3 build.py            # renders + assembly exports
    xvfb-run -a python3 build.py --hires    # also the 5600 x 4000 render
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh
import vtk

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "onshape"))
sys.path.insert(0, str(HERE))

import hardware  # noqa: E402
import layout  # noqa: E402

COMP = HERE / "components"
ASM_DIR = HERE / "assembly"
RENDER_DIR = HERE / "renders"

IMG_W, IMG_H = 1400, 1000

# June frame: hinge axis along X through (Y_DISP, Z_AUG), outlet towards +Y
Y_DISP, Z_AUG = 125.0, 29.25

# ----- colours (the June palette, so the figure keeps its colour code) ----
COL_PLATE = (0.80, 0.82, 0.86)
COL_BASE = (0.62, 0.66, 0.72)
COL_AUGER = (0.90, 0.76, 0.45)
COL_CAP = (0.30, 0.45, 0.80)
COL_BRACKET = (0.55, 0.72, 0.85)
COL_TAP_COLLAR = (0.70, 0.45, 0.85)
COL_TAP_MOUNT = (0.55, 0.40, 0.70)
COL_PINION = (0.45, 0.70, 0.55)
COL_MOTOR = (0.30, 0.30, 0.35)
COL_SERVO_PINION = (0.50, 0.85, 0.55)
COL_SERVO_BODY = (0.20, 0.20, 0.22)
COL_SOLENOID = (0.60, 0.62, 0.66)
COL_STEEL = (0.76, 0.77, 0.80)

COLOURS = {
    "Baseplate": COL_BASE,
    "Mounting plate": COL_PLATE,
    "Auger": COL_AUGER,
    "Auger cap": COL_CAP,
    "Bracket (rear)": COL_BRACKET,
    "Bracket (front)": COL_BRACKET,
    "Tap collar base (AI)": COL_TAP_MOUNT,
    "Tap collar": COL_TAP_COLLAR,
    "Solenoid (Adafruit 412)": COL_SOLENOID,
    "Stepper pinion": COL_PINION,
    "Stepper (NEMA 11)": COL_MOTOR,
    "Servo pinion (+X)": COL_SERVO_PINION,
    "Servo pinion (-X)": COL_SERVO_PINION,
    "Servo MG996R (+X)": COL_SERVO_BODY,
    "Servo MG996R (-X)": COL_SERVO_BODY,
}

# Provenance of every non-fastener part ("current" = the file the rig was
# printed from; "AI" = the AI-modelled part still on the rig; "purchased" =
# simplified model of a bought part, from its datasheet).
PROVENANCE = {
    "Baseplate": ("current", "Fusion 360 (lab account), https://a360.co/4AOA7sI"),
    "Mounting plate": ("current", "Fusion 360 (lab account), https://a360.co/4xXUj8L"),
    "Auger": ("current", "Fusion 360 (lab account), https://a360.co/4y1oz2H"),
    "Auger cap": ("current", "Fusion 360 (lab account), https://a360.co/4w9kRE5"),
    "Bracket (rear)": ("current", "Fusion 360 (lab account), https://a360.co/46XtYN1"),
    "Bracket (front)": ("current", "Fusion 360 (lab account), https://a360.co/46XtYN1"),
    "Tap collar base (AI)": ("AI", "Copilot coding agent, mount_plate.step from PR #51"),
    "Tap collar": ("current", "Fusion 360 (lab account), https://a360.co/4AIIgyz"),
    "Solenoid (Adafruit 412)": ("purchased", "simplified from the Adafruit 412 datasheet"),
    "Stepper pinion": ("current", "Fusion 360 (lab account), https://a360.co/4yqSHFz"),
    "Stepper (NEMA 11)": ("purchased", "simplified from the 11HS18-0674S datasheet"),
    "Servo pinion (+X)": ("current", "Fusion 360 (lab account), https://a360.co/4dcGSdF"),
    "Servo pinion (-X)": ("current", "Fusion 360 (lab account), https://a360.co/4dcGSdF"),
    "Servo MG996R (+X)": ("purchased", "simplified from the MG996R datasheet"),
    "Servo MG996R (-X)": ("purchased", "simplified from the MG996R datasheet"),
}


def _T(t) -> np.ndarray:
    M = np.eye(4)
    M[:3, 3] = t
    return M


# world (Fusion baseplate frame) -> June render frame
W2J = (_T((0.0, Y_DISP, Z_AUG)) @ np.diag([-1.0, -1.0, 1.0, 1.0])
       @ _T((0.0, -layout.HINGE_Y, -layout.HINGE_Z)))


# --------------------------------------------------------------------------- #
# Geometry
# --------------------------------------------------------------------------- #
_MESH_CACHE: dict = {}


def _polydata(shape) -> vtk.vtkPolyData:
    pd = shape.toVtkPolyData(0.04, 0.2)
    # smooth shading that keeps sharp CAD edges
    n = vtk.vtkPolyDataNormals()
    n.SetInputData(pd)
    n.SetFeatureAngle(35.0)
    n.SplittingOn()
    n.Update()
    return n.GetOutput()


def _step_polydata(rel: str) -> vtk.vtkPolyData:
    if rel not in _MESH_CACHE:
        shp = cq.importers.importStep(str(COMP / rel))
        _MESH_CACHE[rel] = _polydata(cq.Compound.makeCompound(shp.vals()))
    return _MESH_CACHE[rel]


def _fastener_polydata(key: str) -> vtk.vtkPolyData:
    k = "hw:" + key
    if k not in _MESH_CACHE:
        if not hasattr(_fastener_polydata, "models"):
            _fastener_polydata.models = hardware.models()
        _MESH_CACHE[k] = _polydata(_fastener_polydata.models[key][0])
    return _MESH_CACHE[k]


def _vtk_matrix(M: np.ndarray) -> vtk.vtkTransform:
    t = vtk.vtkTransform()
    t.SetMatrix([float(v) for v in M.reshape(-1)])
    return t


def build_parts(tilt_deg: float = 0.0):
    """[(name, polydata in its own frame, colour, June-frame 4x4, group)]."""
    parts = []
    for name, (rel, M) in layout.placements(tilt_deg).items():
        parts.append((name, _step_polydata(rel), COLOURS[name], W2J @ M, "part"))
    for name, key, joint, M in hardware.fastener_placements(tilt_deg):
        parts.append((name, _fastener_polydata(key), COL_STEEL, W2J @ M, "hardware:" + key))
    return parts


def _world_polydata(pd: vtk.vtkPolyData, M: np.ndarray) -> vtk.vtkPolyData:
    f = vtk.vtkTransformPolyDataFilter()
    f.SetInputData(pd)
    f.SetTransform(_vtk_matrix(M))
    f.Update()
    return f.GetOutput()


def _to_trimesh(pd: vtk.vtkPolyData) -> trimesh.Trimesh:
    tri = vtk.vtkTriangleFilter()
    tri.SetInputData(pd)
    tri.Update()
    pd = tri.GetOutput()
    from vtkmodules.util.numpy_support import vtk_to_numpy
    v = vtk_to_numpy(pd.GetPoints().GetData()).astype(float)
    f = vtk_to_numpy(pd.GetPolys().GetData()).reshape(-1, 4)[:, 1:]
    return trimesh.Trimesh(v, f, process=False)


# --------------------------------------------------------------------------- #
# Rendering — same material settings as the June renderer
# --------------------------------------------------------------------------- #
def _actor(pd: vtk.vtkPolyData, colour, M: np.ndarray, metal: bool = False) -> vtk.vtkActor:
    m = vtk.vtkPolyDataMapper()
    m.SetInputData(pd)
    a = vtk.vtkActor()
    a.SetMapper(m)
    p = a.GetProperty()
    p.SetColor(*colour)
    p.SetSpecular(0.6 if metal else 0.3)
    p.SetSpecularPower(30 if metal else 15)
    a.SetUserTransform(_vtk_matrix(M))
    return a


def make_renderer(parts, size=(IMG_W, IMG_H)):
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.97, 0.97, 0.98)
    for _, pd, colour, M, group in parts:
        ren.AddActor(_actor(pd, colour, M, metal=group.startswith("hardware")))
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(*size)
    win.AddRenderer(ren)
    return ren, win


# The June az = 90 camera *after* its ResetCamera() (which depends on the
# scene bounds).  Pinning it keeps the render at the reference viewpoint
# and scale whatever the parts' bounds are.
JUNE_AZ090_CAMERA = dict(
    position=(468.80419373499785, 491.50419068324004, 281.40571665756363),
    focal_point=(0.0, 22.699996948242188, 0.12320041656496983),
    view_up=(0.0, 0.0, 1.0),
    view_angle=30.0,
)


def set_reference_camera(ren):
    cam = ren.GetActiveCamera()
    cam.SetPosition(*JUNE_AZ090_CAMERA["position"])
    cam.SetFocalPoint(*JUNE_AZ090_CAMERA["focal_point"])
    cam.SetViewUp(*JUNE_AZ090_CAMERA["view_up"])
    cam.SetViewAngle(JUNE_AZ090_CAMERA["view_angle"])
    ren.ResetCameraClippingRange()


def set_iso_camera(ren, azimuth_deg=90.0, elevation_frac=0.6, reset=True):
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(0, 0, Z_AUG)
    diag = 380.0
    ox, oy = diag, -diag
    a = math.radians(azimuth_deg)
    rx = ox * math.cos(a) - oy * math.sin(a)
    ry = ox * math.sin(a) + oy * math.cos(a)
    cam.SetPosition(rx, ry, Z_AUG + diag * elevation_frac)
    cam.SetViewUp(0, 0, 1)
    if reset:
        ren.ResetCamera()


def write_png(win, out_path: Path, scale: int = 1):
    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    if scale > 1:
        w2i.SetScale(scale)
    w2i.SetInputBufferTypeToRGBA()
    w2i.ReadFrontBufferOff()
    w2i.Update()
    w = vtk.vtkPNGWriter()
    w.SetFileName(str(out_path))
    w.SetInputConnection(w2i.GetOutputPort())
    w.Write()
    print(f"  -> {out_path.relative_to(HERE)}")


def project(ren, win, pts) -> list[tuple[float, float]]:
    """June-frame points -> (x, y) pixel coords with the origin at the top left."""
    win.Render()
    c = vtk.vtkCoordinate()
    c.SetCoordinateSystemToWorld()
    h = win.GetSize()[1]
    out = []
    for p in pts:
        c.SetValue(*p)
        x, y = c.GetComputedDoubleDisplayValue(ren)
        out.append((x, h - y))
    return out


def _J(M: np.ndarray, p) -> tuple[float, float, float]:
    return tuple(float(v) for v in (W2J @ M @ np.array([*p, 1.0]))[:3])


def anchor_points(tilt_deg: float = 0.0) -> dict[str, tuple[float, float, float]]:
    """June-frame points the annotation leaders point at."""
    P = {n: M for n, (_, M) in layout.placements(tilt_deg).items()}
    gear_tip_r = (44 + 2) * 1.0 / 2          # auger's 44 T module-1 gear
    hinge_gear_tip_r = 38.94 / 2              # mounting plate's 28 T gears
    sol_top_z = 31.05                         # plunger (spring) end, solenoid frame
    return {
        "Rotation": _J(P["Auger"], (0.0, gear_tip_r, layout.AUGER_GEAR_FROM_OUTLET)),
        "Tapping": _J(P["Solenoid (Adafruit 412)"], (0.0, -7.0, sol_top_z)),
        "Tilt": _J(np.eye(4), (47.95, layout.HINGE_Y, layout.HINGE_Z + hinge_gear_tip_r)),
        "Outlet": _J(P["Auger"], (0.0, 0.0, 0.0)),
        "Cap": _J(P["Auger"], (0.0, 0.0, layout.AUGER_LEN + 2.0)),
    }


def powder_stream_points(outlet, n: int = 150, drop: float = 95.0, seed: int = 165):
    """June-frame points for the drawn powder stream: out of the Ø3 hole in
    the centre of the outlet's end face, then falling and spreading under
    gravity (the auger is horizontal at tilt 0)."""
    rng = np.random.default_rng(seed)
    x0, y0, z0 = outlet
    t = np.sort(rng.random(n)) ** 1.3
    z = z0 - 2.0 - t * drop
    spread = 0.6 + 7.0 * t
    x = x0 + rng.normal(0.0, 1.0, n) * spread
    y = y0 + 3.0 + 6.0 * np.sqrt(t) + rng.normal(0.0, 1.0, n) * spread * 0.6
    return [tuple(map(float, p)) for p in zip(x, y, z)]


def export_assembly(parts) -> None:
    """GLB (one node per part, coloured) and a merged STL, June frame, mm."""
    scene = trimesh.Scene()
    merged = []
    for name, pd, colour, M, _ in parts:
        tm = _to_trimesh(_world_polydata(pd, M))
        rgba = (np.array(list(colour) + [1.0]) * 255).astype(np.uint8)
        tm.visual.face_colors = np.tile(rgba, (len(tm.faces), 1))
        scene.add_geometry(tm, node_name=name, geom_name=name)
        merged.append(tm)
    scene.export(str(ASM_DIR / "full_assembly.glb"))
    trimesh.util.concatenate(merged).export(str(ASM_DIR / "full_assembly.stl"))
    print("  -> assembly/full_assembly.glb, assembly/full_assembly.stl")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hires", action="store_true", help="also write a 4x (5600x4000) render")
    args = ap.parse_args()
    ASM_DIR.mkdir(exist_ok=True)
    RENDER_DIR.mkdir(exist_ok=True)

    for tilt in (0.0, 22.5, 45.0):
        parts = build_parts(tilt)
        ren, win = make_renderer(parts)
        if tilt == 0:
            set_reference_camera(ren)   # the reference figure's exact view
        else:
            set_iso_camera(ren)         # same direction, re-fitted to the tilt
        tag = f"tilt{tilt:g}".replace(".", "p")
        name = "assembly_iso_az090.png" if tilt == 0 else f"assembly_iso_az090_{tag}.png"
        write_png(win, RENDER_DIR / name)
        if tilt == 0:
            anchors = anchor_points(tilt)
            pix = {k: project(ren, win, [p])[0] for k, p in anchors.items()}
            pix["stream"] = project(ren, win, powder_stream_points(anchors["Outlet"]))
            (RENDER_DIR / "anchors_az090.json").write_text(json.dumps(pix, indent=1) + "\n")
            if args.hires:
                write_png(win, RENDER_DIR / "assembly_iso_az090_hires.png", scale=4)
            # front view from the outlet end, to compare with the rig photos
            cam = ren.GetActiveCamera()
            cam.SetFocalPoint(0, 40, Z_AUG)
            cam.SetPosition(0, 420, Z_AUG + 140)
            cam.SetViewUp(0, 0, 1)
            ren.ResetCamera()
            write_png(win, RENDER_DIR / "assembly_front_from_outlet.png")
            export_assembly(parts)

    manifest = {n: {"status": s, "source": src} for n, (s, src) in PROVENANCE.items()}
    for r in hardware.bom_rows():
        manifest[r["desc"]] = {"status": "purchased", "qty": r["qty"],
                               "source": (f"McMaster-Carr {r['mcmaster']}" if r["mcmaster"]
                                          else "ISO-dimension stand-in"),
                               "joints": r["joints"]}
    (ASM_DIR / "parts_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("  -> assembly/parts_manifest.json")


if __name__ == "__main__":
    main()
