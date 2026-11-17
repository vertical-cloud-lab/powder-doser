"""Auger tube: the rotating powder reservoir and conveyor.

Recreates components/fusion-step/auger.step (Fusion 360 body "Shaft") in the
frame it was exported in: tube axis +Z, outlet face at z = 0, cap end at
z = TUBE_LENGTH. The whole tube turns in two split-clamp brackets, driven by
a 20T stepper pinion meshing with the 44T gear moulded onto it.

Interior, from the outlet up:
* z = 0 .. 12: outlet funnel. The bore closes conically (36.87 deg half-angle)
  from the 21 mm bore to a 3 mm exit, around the conical tip of a central
  8 mm core shaft (16.70 deg, 0.8 mm tip), leaving an annular outlet
  (ID 0.8, OD 3.0) in the end face.
* z = 0 .. 83.33: a right-handed helical flight, 0.5 mm thick (axially),
  joins the core to the bore wall: 8 turns, pitch 10.416 mm, starting on +X
  at the outlet face. Turning the tube anticlockwise about +Z (seen from the
  cap end) conveys powder towards the outlet.
* z = 83.33 .. 250: open bore, the powder reservoir, closed by the cap
  screwed onto the right-handed 3.5 mm-pitch thread at z = 225 .. 250.
"""
from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import step, stl

from lib.gears import spur_gear

# tube
TUBE_LENGTH = 250.0
TUBE_OD = 25.0
BORE_D = 21.0                    # 2 mm wall
# outlet funnel, z = 0 .. FUNNEL_LENGTH
FUNNEL_LENGTH = 12.0
OUTLET_D = 3.0                   # funnel exit in the end face
# central core shaft, conical tip inside the funnel
CORE_D = 8.0
CORE_TIP_D = 0.8                 # at z = 0
CORE_TOP_Z = 83.333
# helical flight, right-handed, swept from +X at z = 0
FLIGHT_TURNS = 8
FLIGHT_RISE = 83.33              # total rise of the turns
FLIGHT_PITCH = FLIGHT_RISE / FLIGHT_TURNS
FLIGHT_THICKNESS = 0.5           # axial
FLIGHT_ROOT_D = CORE_TIP_D       # flight runs from the core-tip radius to the bore
# drive gear, 44T module 1 (meshes the 20T stepper pinion)
GEAR_MODULE = 1.0
GEAR_TEETH = 44
GEAR_WIDTH = 10.0
GEAR_Z0 = 78.333                 # face centred 83.333 mm from the outlet
# cap thread: right-handed, rounded trapezoid, minor dia below the shoulder
THREAD_SHOULDER_Z = 225.0
THREAD_MAJOR_D = 26.0
THREAD_MINOR_D = 23.0
THREAD_PITCH = 3.5
THREAD_ROOT_WIDTH = 2.0          # tooth width on the minor diameter
THREAD_FLANK_SLOPE = 1.0 / 6.0   # axial per radial (flanks 9.46 deg off radial)
THREAD_CREST_ROUND = 0.5         # radius on both crest corners
THREAD_START_Z = 223.35          # crest centre where the thread starts, on +X
# how far added features sink into the wall they join (no coincident faces)
SINK = 0.5


def _xz(points: list[tuple[float, float]]) -> bd.Face:
    """Closed polygon face in the XZ half-plane, points given as (r, z)."""
    return bd.Face(bd.Wire.make_polygon([(r, 0.0, z) for r, z in points], close=True))


def _helical(profile: bd.Face, pitch: float, turns: float, z0: float) -> bd.Solid:
    """Right-handed screw sweep of an XZ-plane profile, starting on +X."""
    path = bd.Edge.make_helix(pitch, pitch * turns, 5.0, center=(0, 0, z0))
    return bd.sweep(profile, path, is_frenet=True).solids()[0]


def _tube() -> bd.Solid:
    r_out, r_bore = TUBE_OD / 2, BORE_D / 2
    return bd.revolve(_xz([
        (OUTLET_D / 2, 0.0), (r_out, 0.0), (r_out, THREAD_SHOULDER_Z),
        (THREAD_MINOR_D / 2, THREAD_SHOULDER_Z), (THREAD_MINOR_D / 2, TUBE_LENGTH),
        (r_bore, TUBE_LENGTH), (r_bore, FUNNEL_LENGTH),
    ]), bd.Axis.Z).solids()[0]


def _core() -> bd.Solid:
    return bd.revolve(_xz([
        (0.0, 0.0), (CORE_TIP_D / 2, 0.0), (CORE_D / 2, FUNNEL_LENGTH),
        (CORE_D / 2, CORE_TOP_Z), (0.0, CORE_TOP_Z),
    ]), bd.Axis.Z).solids()[0]


def _flight() -> bd.Solid:
    r0, r1 = FLIGHT_ROOT_D / 2, BORE_D / 2 + SINK
    return _helical(_xz([(r0, 0.0), (r1, 0.0), (r1, FLIGHT_THICKNESS), (r0, FLIGHT_THICKNESS)]),
                    FLIGHT_PITCH, FLIGHT_TURNS, 0.0)


def _gear() -> bd.Solid:
    gear = spur_gear(GEAR_MODULE, GEAR_TEETH, GEAR_WIDTH, bore=TUBE_OD - 2 * SINK)
    return gear.moved(bd.Location((0, 0, GEAR_Z0))).solids()[0]


def _thread() -> bd.Solid:
    r_root, r_crest = THREAD_MINOR_D / 2, THREAD_MAJOR_D / 2
    half_root = THREAD_ROOT_WIDTH / 2
    half_crest = half_root - (r_crest - r_root) * THREAD_FLANK_SLOPE
    r_in = r_root - SINK
    half_in = half_root + SINK * THREAD_FLANK_SLOPE
    z = THREAD_START_Z
    profile = _xz([(r_in, z - half_in), (r_crest, z - half_crest),
                   (r_crest, z + half_crest), (r_in, z + half_in)])
    crest = [v for v in profile.vertices() if abs(v.X - r_crest) < 1e-9]
    profile = profile.fillet_2d(THREAD_CREST_ROUND, crest)
    turns = math.ceil((TUBE_LENGTH + half_in - THREAD_START_Z) / THREAD_PITCH)
    coil = _helical(profile, THREAD_PITCH, turns, z)
    # trim flush with the cap end of the tube
    keep = bd.Cylinder(r_crest + 1, TUBE_LENGTH,
                       align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    return coil.intersect(keep).solids()[0]


@step(out="../../STEP/parts/auger.step")
@stl(out="../../STL/parts/auger.stl")
def auger():
    body = _tube().fuse(_core(), _flight(), _gear(), _thread()).clean()
    body = body.solids()[0]
    body.label = "auger"
    return body


if __name__ == "__main__":
    auger()
