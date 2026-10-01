"""Full powder-doser assembly with the current parts, rendered from the
same camera as the annotated overview render (issue #165).

The June render (``cad/mounting-plate-assembly/render_assembly.py`` on
``copilot/add-servo-angle-control`` @ 97521d2, ``assembly_iso_az090.png``)
is reproduced pixel-for-pixel by this script when every part is left at
its June version, so any difference in the new render comes from a part
swap, not from the camera or lighting.

Parts that changed since June (see ``PARTS`` and README.md):

  * auger: Sam's Fusion 360 threaded storage auger, with the 44-tooth
    module-1 gear printed on the tube and the flight on the outlet end only
  * screw-on cap: Sam's Fusion 360 cap
  * stepper pinion: 20 teeth, module 1 (the Fusion redesign's spec,
    regenerated here because the Fusion file isn't shared)
  * solenoid: the 12 V open-frame push-pull solenoid on the rig
    (TAU0730TM-14 label), modelled from photos
  * tap collar: an approximation of the current collar (ring plus an
    angled solenoid cradle), modelled from the 11 Sep photo until the
    real file is exported

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
sys.path.insert(0, str(HERE / "parts" / "june"))

from cad_model import (  # noqa: E402  (June parametric source, vendored)
    GEAR_CENTRE_DISTANCE, GEAR_HINGE_TIP_D, GEAR_X_CENTRE, MG996R_BODY_H, MG996R_BODY_L, MG996R_BODY_T,
    MG996R_SPLINE_Y_OFFSET, MOTOR_FACE_Y, NEMA11_BODY_L, NEMA11_BODY_W,
    PINION_X_LO, PINION_X_LO_NEG, PINION_Y, PINION_Z, PLATE_X_CENTRE,
    SERVO_BODY_X_LO, SERVO_BODY_X_LO_NEG,
    X_MOTOR, Y_BRK_FRONT, Y_BRK_REAR, Y_DISP, Y_GEAR_BAND, Y_TAP, Z_AUG,
    Z_MOTOR, _build_spur_gear, build_baseplate, build_hinge_pin,
    build_mounting_plate, build_servo_pinion,
)

PARTS_DIR = HERE / "parts"
GEN_DIR = HERE / "parts" / "generated"
ASM_DIR = HERE / "assembly"
RENDER_DIR = HERE / "renders"

IMG_W, IMG_H = 1400, 1000

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
COL_PIN = (0.85, 0.55, 0.20)
COL_SERVO_PINION = (0.50, 0.85, 0.55)
COL_SERVO_BODY = (0.20, 0.20, 0.22)
COL_SOL_FRAME = (0.78, 0.79, 0.81)
COL_SOL_COIL = (0.16, 0.20, 0.42)

# ----- current-design dimensions ------------------------------------------
# Fusion stepper pinion (video EO9qnYssKRQ): 20 T, module 1, so it meshes
# the auger's 44 T module-1 gear at (20 + 44) / 2 = 32 mm, the same centre
# distance as June.
PINION_TEETH = 20
PINION_MODULE = 1.0
PINION_FACE_W = 16.0
AUGER_GEAR_TEETH = 44
assert abs((PINION_TEETH + AUGER_GEAR_TEETH) * PINION_MODULE / 2
           - GEAR_CENTRE_DISTANCE) < 1e-9

# Approximate current tap collar (from the 11 Sep 2026 photo in #156):
# a clamp ring with a cradle holding the solenoid at SOL_TILT_DEG from
# vertical, leaning away from the stepper (towards -X).
COLLAR_ID = 25.4
COLLAR_OD = 33.5           # same OD as the June collar, so it sits on the
COLLAR_W = 16.0            # June hard-stop mount plate unchanged
SOL_TILT_DEG = 40.0
# 12 V open-frame push-pull solenoid, sized from the photos against the
# 25 mm tube: U-frame + coil, plunger with return spring out the top.
SOL_FRAME_L = 27.0         # along the plunger axis
SOL_FRAME_W = 14.0         # across the tube axis
SOL_FRAME_T = 12.0         # along the tube axis
SOL_PLUNGER_D = 6.0
SOL_PLUNGER_OUT = 9.0      # plunger stick-out past the frame (spring end)
SOL_SPRING_D = 8.5
CRADLE_WALL = 2.0
CRADLE_DEPTH = 10.0        # how far the cradle walls run up the frame
SOL_BASE_R = COLLAR_OD / 2 + 1.5   # frame bottom, radially from the axis

# Fusion auger STL: axis +Z, outlet at z = 0, 250 mm long, 44 T gear at
# z = 78.33-88.33 (centre 83.33 = L/3, exactly where June put its gear
# band), external cap thread at z = 222.5-250.  Cap STL: closed end at
# z = 0..2, open end at z = -25, so it seats with z = 0 at the tube end.
AUGER_LEN = 250.0
CAP_SEAT_Z = AUGER_LEN

# Provenance of every part.  "current" = the file the rig was printed
# from; "spec" = regenerated from the published spec; "approx" = modelled
# from photos; "june" = the June AI-era part, still a stand-in.
PARTS = {
    "auger": ("current", "Fusion 360 (Sam), 'Threaded Auger Final.stl', #117 zip"),
    "cap": ("current", "Fusion 360 (Sam), 'Cap Final.stl', #117 zip"),
    "stepper_pinion": ("spec", "20 T module 1 per the Fusion redesign video EO9qnYssKRQ"),
    "solenoid": ("approx", "12 V push-pull solenoid (TAU0730TM-14 label), sized from photos"),
    "tap_collar": ("approx", "ring + angled solenoid cradle, from the 11 Sep photo (#156)"),
    "tap_collar_mount": ("june", "June hard-stop plate (PR #51); Fusion tap collar not shared"),
    "brackets": ("june", "June split-collar brackets (PR #47); rig uses the Fusion flexible brackets"),
    "mounting_plate": ("june", "June CadQuery (PR #66); Fusion redesign (v8my5C7718w) not shared"),
    "baseplate": ("june", "June CadQuery (PR #66); Fusion redesign (zOh_KagOwOU) not shared"),
    "servo_pinions": ("june", "June 14 T (2:1 with the 28 T hinge gears); Fusion version not shared"),
    "hinge_pins": ("june", "June M5 pins"),
    "nema11": ("june", "NEMA-11 body as a box"),
    "mg996r": ("june", "MG996R bodies as boxes"),
}


# --------------------------------------------------------------------------- #
# Geometry helpers
# --------------------------------------------------------------------------- #
def stepper_pinion() -> cq.Workplane:
    """20 T module-1 pinion, axis +Z from z = 0 to PINION_FACE_W, Ø5 D-bore.

    Phased by half a tooth so a gap faces the auger gear: the Fusion
    gear has a tooth tip at local +X, and the pinion sits on +X, so the
    mesh point is at the pinion's 180° where an unphased even-tooth gear
    would put a tooth.
    """
    gear = _build_spur_gear(PINION_TEETH, PINION_MODULE, PINION_FACE_W, 5.0,
                            flat=True, pa_deg=20.0, backlash=0.2)
    return gear.rotate((0, 0, 0), (0, 0, 1), 360.0 / PINION_TEETH / 2.0)


def _radial_frame(r: float):
    """Point at radius r on the solenoid's radial line (tube local XZ)."""
    a = math.radians(SOL_TILT_DEG)
    return (-r * math.sin(a), 0.0, r * math.cos(a))


def tap_collar_approx() -> cq.Workplane:
    """Approximate current tap collar in a local frame with the tube axis
    along +Y through the origin.  Ring, clamp lips at the split, and a
    cradle that holds the solenoid radially at SOL_TILT_DEG from vertical.
    """
    ring = (cq.Workplane("XZ").circle(COLLAR_OD / 2).circle(COLLAR_ID / 2)
            .extrude(COLLAR_W / 2, both=True))
    # split + two clamp lips on the stepper side, 45° above horizontal
    lip_len, lip_t, gap = 6.0, 3.0, 2.0
    lip_a, lip_b = (
        cq.Workplane("XY").box(lip_len, lip_t, COLLAR_W)
        .rotate((0, 0, 0), (1, 0, 0), 90)
        .translate((COLLAR_OD / 2 + lip_len / 2 - 1.0, 0, s * (gap / 2 + lip_t / 2)))
        for s in (-1, 1))
    lips = lip_a.union(lip_b).rotate((0, 0, 0), (0, 1, 0), -45)
    slot = (cq.Workplane("XY").box(COLLAR_OD, COLLAR_W + 2, gap)
            .translate((COLLAR_OD / 2, 0, 0))
            .rotate((0, 0, 0), (0, 1, 0), -45))
    collar = ring.union(lips).cut(slot)
    # cradle: an open-topped box, axis radial, base on the ring
    in_w, in_t = SOL_FRAME_W + 0.6, SOL_FRAME_T + 0.6
    out_w, out_t = in_w + 2 * CRADLE_WALL, in_t + 2 * CRADLE_WALL
    base_r = COLLAR_OD / 2 - 2.0
    h = (SOL_BASE_R - base_r) + CRADLE_DEPTH
    cradle = (cq.Workplane("XY").box(out_w, out_t, h, centered=(True, True, False))
              .cut(cq.Workplane("XY").box(in_w, in_t, h,
                                          centered=(True, True, False))
                   .translate((0, 0, SOL_BASE_R - base_r)))
              .translate((0, 0, base_r)))
    # plunger clearance hole through the cradle floor
    cradle = cradle.cut(cq.Workplane("XY").circle(SOL_PLUNGER_D / 2 + 0.5)
                        .extrude(h).translate((0, 0, base_r - 1)))
    cradle = cradle.rotate((0, 0, 0), (0, 1, 0), -SOL_TILT_DEG)
    collar = collar.union(cradle).cut(
        cq.Workplane("XZ").circle(COLLAR_ID / 2).extrude(COLLAR_W, both=True))
    return collar


def solenoid_parts() -> tuple[cq.Workplane, cq.Workplane]:
    """(frame + plunger + spring, coil) of the push-pull solenoid, local
    frame as tap_collar_approx(), seated in the cradle."""
    frame = (cq.Workplane("XY")
             .box(SOL_FRAME_W, SOL_FRAME_T, SOL_FRAME_L, centered=(True, True, False))
             .cut(cq.Workplane("XY")
                  .box(SOL_FRAME_W - 2.4, SOL_FRAME_T + 2, SOL_FRAME_L - 2.4,
                       centered=(True, True, False))
                  .translate((0, 0, 1.2))))
    plunger = (cq.Workplane("XY").circle(SOL_PLUNGER_D / 2)
               .extrude(SOL_FRAME_L + SOL_PLUNGER_OUT))
    spring = None
    for k in range(5):
        coil_turn = (cq.Workplane("XY").circle(SOL_SPRING_D / 2)
                     .circle(SOL_SPRING_D / 2 - 0.9).extrude(0.9)
                     .translate((0, 0, SOL_FRAME_L + 0.6 + 1.5 * k)))
        spring = coil_turn if spring is None else spring.union(coil_turn)
    washer = (cq.Workplane("XY").circle(SOL_SPRING_D / 2 + 0.6)
              .extrude(1.0).translate((0, 0, SOL_FRAME_L + SOL_PLUNGER_OUT - 1.0)))
    metal = frame.union(plunger).union(spring).union(washer)
    coil = (cq.Workplane("XY").circle(SOL_FRAME_T / 2 - 0.3)
            .extrude(SOL_FRAME_L - 4.0).translate((0, 0, 2.0)))
    out = []
    for part in (metal, coil):
        out.append(part.translate((0, 0, SOL_BASE_R))
                   .rotate((0, 0, 0), (0, 1, 0), -SOL_TILT_DEG))
    return out[0], out[1]


# --------------------------------------------------------------------------- #
# VTK helpers (same material settings as the June renderer)
# --------------------------------------------------------------------------- #
def _actor_from_polydata(pd: vtk.vtkPolyData, colour) -> vtk.vtkActor:
    m = vtk.vtkPolyDataMapper()
    m.SetInputData(pd)
    a = vtk.vtkActor()
    a.SetMapper(m)
    a.GetProperty().SetColor(*colour)
    a.GetProperty().SetSpecular(0.3)
    a.GetProperty().SetSpecularPower(15)
    return a


def _stl_polydata(path: Path) -> vtk.vtkPolyData:
    r = vtk.vtkSTLReader()
    r.SetFileName(str(path))
    r.Update()
    return r.GetOutput()


def _shape_polydata(shape) -> vtk.vtkPolyData:
    if isinstance(shape, cq.Workplane):
        shape = shape.val()
    return shape.toVtkPolyData(0.1, 0.5)


def _transform(*ops) -> vtk.vtkTransform:
    t = vtk.vtkTransform()
    t.PostMultiply()
    for op, *args in ops:
        getattr(t, op)(*args)
    return t


def _tilt(tilt_deg: float, pre: vtk.vtkTransform | None = None) -> vtk.vtkTransform:
    """(pre) then rotate about the hinge axis (global X through Y_DISP, Z_AUG)."""
    t = vtk.vtkTransform()
    t.PostMultiply()
    if pre is not None:
        t.Concatenate(pre)
    t.Translate(0, -Y_DISP, -Z_AUG)
    t.RotateX(-tilt_deg)
    t.Translate(0, Y_DISP, Z_AUG)
    return t


AUGER_FRAME = (("RotateX", 90), ("Translate", 0, Y_DISP, Z_AUG))


def build_parts(tilt_deg: float = 0.0) -> list[tuple[str, vtk.vtkPolyData, tuple, vtk.vtkTransform | None]]:
    """(name, polydata in its own frame, colour, transform) for every part."""
    parts = []

    def add(name, pd, colour, t=None):
        parts.append((name, pd, colour, t))

    add("baseplate", _shape_polydata(build_baseplate()), COL_BASE)
    add("mounting_plate", _shape_polydata(build_mounting_plate()), COL_PLATE, _tilt(tilt_deg))

    # auger + cap (Fusion): native axis +Z, outlet at z = 0 -> along -Y
    # from the outlet at Y_DISP, centred at X = 0, Z = Z_AUG (June frame).
    add("auger", _stl_polydata(PARTS_DIR / "fusion/threaded-auger-final.stl"),
        COL_AUGER, _tilt(tilt_deg, _transform(*AUGER_FRAME)))
    add("cap", _stl_polydata(PARTS_DIR / "fusion/cap-final.stl"), COL_CAP,
        _tilt(tilt_deg, _transform(("Translate", 0, 0, CAP_SEAT_Z), *AUGER_FRAME)))

    for i, cy in enumerate((Y_BRK_FRONT, Y_BRK_REAR)):
        add(f"bracket_{'front' if i == 0 else 'rear'}",
            _stl_polydata(PARTS_DIR / "june/auger-bracket.stl"), COL_BRACKET,
            _tilt(tilt_deg, _transform(("Translate", 0, cy, 0))))
    add("tap_collar_mount", _stl_polydata(PARTS_DIR / "june/tap-collar-mount-plate.stl"),
        COL_TAP_MOUNT, _tilt(tilt_deg, _transform(("Translate", 0, Y_TAP, 0))))

    collar_t = _tilt(tilt_deg, _transform(("Translate", 0, Y_TAP, Z_AUG)))
    add("tap_collar", _shape_polydata(tap_collar_approx()), COL_TAP_COLLAR, collar_t)
    sol_metal, sol_coil = solenoid_parts()
    add("solenoid", _shape_polydata(sol_metal), COL_SOL_FRAME, collar_t)
    add("solenoid_coil", _shape_polydata(sol_coil), COL_SOL_COIL, collar_t)

    # 20 T pinion on the NEMA-11 shaft, centred on the auger gear face.
    pin_t = _tilt(tilt_deg, _transform(
        ("Translate", 0, 0, -PINION_FACE_W / 2), ("RotateX", 90),
        ("Translate", X_MOTOR, Y_GEAR_BAND, Z_AUG)))
    add("stepper_pinion", _shape_polydata(stepper_pinion()), COL_PINION, pin_t)
    # NEMA-11 face stays on the June motor-mount block; the 2 mm gap to
    # the pinion is the exposed shaft.
    motor = cq.Workplane("XY").box(NEMA11_BODY_W, NEMA11_BODY_L, NEMA11_BODY_W)
    add("nema11", _shape_polydata(motor), COL_MOTOR, _tilt(tilt_deg, _transform(
        ("Translate", X_MOTOR, MOTOR_FACE_Y - NEMA11_BODY_L / 2, Z_MOTOR))))

    add("hinge_pins", _shape_polydata(build_hinge_pin()), COL_PIN,
        _transform(("Translate", 0, Y_DISP, Z_AUG)))
    for side, x_lo in (("pos", PINION_X_LO), ("neg", PINION_X_LO_NEG)):
        add(f"servo_pinion_{side}", _shape_polydata(
            build_servo_pinion().translate((x_lo, PINION_Y, PINION_Z))), COL_SERVO_PINION)
    for side, x_lo in (("pos", SERVO_BODY_X_LO), ("neg", SERVO_BODY_X_LO_NEG)):
        body = (cq.Workplane("XY")
                .box(MG996R_BODY_H, MG996R_BODY_L, MG996R_BODY_T, centered=(False, False, True))
                .translate((x_lo, PINION_Y - MG996R_SPLINE_Y_OFFSET, PINION_Z)))
        add(f"mg996r_{side}", _shape_polydata(body), COL_SERVO_BODY)
    return parts


def _world_polydata(pd: vtk.vtkPolyData, t: vtk.vtkTransform | None) -> vtk.vtkPolyData:
    if t is None:
        return pd
    f = vtk.vtkTransformPolyDataFilter()
    f.SetInputData(pd)
    f.SetTransform(t)
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
# Rendering — camera identical to the June ``render_assembly_view('iso',
# azimuth_deg=90)`` that produced the reference image.
# --------------------------------------------------------------------------- #
def make_renderer(parts, size=(IMG_W, IMG_H)):
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.97, 0.97, 0.98)
    for _, pd, colour, t in parts:
        a = _actor_from_polydata(pd, colour)
        if t is not None:
            a.SetUserTransform(t)
        ren.AddActor(a)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(*size)
    win.AddRenderer(ren)
    return ren, win


# The June az = 90 camera *after* its ResetCamera() (which depends on the
# scene bounds).  Pinning it keeps the new render at exactly the reference
# viewpoint and scale even though the new parts change the bounds.
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
    cam.SetFocalPoint(PLATE_X_CENTRE, 0, Z_AUG)
    diag = 380.0
    ox, oy = diag, -diag
    a = math.radians(azimuth_deg)
    rx = ox * math.cos(a) - oy * math.sin(a)
    ry = ox * math.sin(a) + oy * math.cos(a)
    cam.SetPosition(PLATE_X_CENTRE + rx, ry, Z_AUG + diag * elevation_frac)
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


def project(ren, win, pts_world) -> list[tuple[float, float]]:
    """World points -> (x, y) pixel coords with the origin at the top left."""
    win.Render()
    c = vtk.vtkCoordinate()
    c.SetCoordinateSystemToWorld()
    h = win.GetSize()[1]
    out = []
    for p in pts_world:
        c.SetValue(*p)
        x, y = c.GetComputedDoubleDisplayValue(ren)
        out.append((x, h - y))
    return out


def anchor_points(tilt_deg: float = 0.0) -> dict[str, tuple[float, float, float]]:
    """World-space points the annotation leaders point at."""
    def tilted(p):
        t = _tilt(tilt_deg)
        return t.TransformPoint(p)
    gear_r = (AUGER_GEAR_TEETH + 2) * PINION_MODULE / 2
    sol_top = np.array(_radial_frame(SOL_BASE_R + SOL_FRAME_L + SOL_PLUNGER_OUT))
    return {
        "Rotation": tilted((0.0, Y_GEAR_BAND, Z_AUG + gear_r)),
        "Tapping": tilted((sol_top[0], Y_TAP + sol_top[1], Z_AUG + sol_top[2])),
        "Tilt": (-GEAR_X_CENTRE, Y_DISP, Z_AUG + GEAR_HINGE_TIP_D / 2),
        "Outlet": tilted((0.0, Y_DISP, Z_AUG)),
        "Cap": tilted((0.0, Y_DISP - AUGER_LEN - 2.0, Z_AUG)),
    }


def powder_stream_points(n: int = 170, drop: float = 130.0, seed: int = 165):
    """World points for the drawn powder stream: out of the Ø3 outlet hole
    in the centre of the end face, then falling and spreading under gravity
    (the auger is horizontal at tilt 0)."""
    rng = np.random.default_rng(seed)
    t = np.sort(rng.random(n)) ** 1.3
    z = Z_AUG - 2.0 - t * drop
    spread = 0.6 + 7.0 * t
    x = rng.normal(0.0, 1.0, n) * spread
    y = Y_DISP + 3.0 + 6.0 * np.sqrt(t) + rng.normal(0.0, 1.0, n) * spread * 0.6
    return [tuple(map(float, p)) for p in zip(x, y, z)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hires", action="store_true", help="also write a 4x (5600x4000) render")
    args = ap.parse_args()
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    ASM_DIR.mkdir(exist_ok=True)
    RENDER_DIR.mkdir(exist_ok=True)

    # generated parts, in their own frames, for printing / inspection
    cq.exporters.export(stepper_pinion(), str(GEN_DIR / "stepper-pinion-20t-m1.stl"))
    cq.exporters.export(tap_collar_approx(), str(GEN_DIR / "tap-collar-approx.stl"))
    sol_metal, sol_coil = solenoid_parts()
    cq.exporters.export(sol_metal.union(sol_coil), str(GEN_DIR / "solenoid-12v-approx.stl"))

    for tilt in (0.0, 22.5, 45.0):
        parts = build_parts(tilt)
        ren, win = make_renderer(parts)
        set_reference_camera(ren)
        tag = f"tilt{tilt:g}".replace(".", "p")
        name = "assembly_iso_az090.png" if tilt == 0 else f"assembly_iso_az090_{tag}.png"
        write_png(win, RENDER_DIR / name)
        if tilt == 0:
            pix = {k: project(ren, win, [p])[0] for k, p in anchor_points(tilt).items()}
            pix["stream"] = project(ren, win, powder_stream_points())
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

            # assembly exports in the June frame (mm): one colour per part
            scene = trimesh.Scene()
            merged = []
            for name_, pd, colour, t in parts:
                tm = _to_trimesh(_world_polydata(pd, t))
                rgba = (np.array(list(colour) + [1.0]) * 255).astype(np.uint8)
                tm.visual.face_colors = np.tile(rgba, (len(tm.faces), 1))
                scene.add_geometry(tm, node_name=name_, geom_name=name_)
                merged.append(tm)
            scene.export(str(ASM_DIR / "full_assembly.glb"))
            trimesh.util.concatenate(merged).export(str(ASM_DIR / "full_assembly.stl"))
            print("  -> assembly/full_assembly.glb, assembly/full_assembly.stl")

    manifest = {k: {"status": s, "source": src} for k, (s, src) in PARTS.items()}
    (ASM_DIR / "parts_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("  -> assembly/parts_manifest.json")


if __name__ == "__main__":
    main()
