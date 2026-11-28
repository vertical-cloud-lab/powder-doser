"""Assemblies of the ten apparatuses: printed parts (out/stl), stand-ins for bought parts, and context
(the HR-100A, the doser's auger and module), with the order and captions of the assembly steps.

Each assembly is a list of Comp. `step` is the assembly step in which a component appears; it flies in
along `explode` (mm). `ASSEMBLIES[key]["steps"]` holds one caption per step. Frames: z up, mm; the
balance pan centre is the origin for tests that sit in the HR-100A.

    python assemblies.py            # renders out/renders/<key>.png (iso view of each assembly)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np
import trimesh
from trimesh.creation import box as tbox, cylinder as tcyl, annulus as tann

import parts as P

HERE = Path(__file__).resolve().parent
STL = HERE / "out" / "stl"
DOSER = Path("/tmp/doser-cad")   # PR #176's text-to-cad export (git show 509a0bf:cad/text-to-cad/...)

PRINTED = "#2a9d8f"
BOUGHT = "#7b5ea7"
METAL = "#a7adb4"
STEEL = "#c9ced3"
GLASS = "#bfe3f2"
DOSERC = "#9a9a9a"
PCB = "#1f7a3a"
DARK = "#333333"


def T(tx=0.0, ty=0.0, tz=0.0, rx=0.0, ry=0.0, rz=0.0):
    M = np.eye(4)
    for ang, ax in ((rx, [1, 0, 0]), (ry, [0, 1, 0]), (rz, [0, 0, 1])):
        if ang:
            M = trimesh.transformations.rotation_matrix(math.radians(ang), ax) @ M
    M[:3, 3] += [tx, ty, tz]
    return M


@dataclass
class Comp:
    label: str
    mesh: trimesh.Trimesh
    color: str
    M: np.ndarray
    step: int = 0
    explode: tuple = (0.0, 0.0, 60.0)
    kind: str = "printed"          # printed | bought | context
    opacity: float = 1.0
    group: str = ""                # name used by the SOP animations to move parts
    meta: dict = field(default_factory=dict)


@lru_cache(maxsize=None)
def stl(name: str) -> trimesh.Trimesh:
    return trimesh.load(STL / f"{name}.stl", force="mesh")


def bx(x0, x1, y0, y1, z0, z1):
    m = tbox(extents=[x1 - x0, y1 - y0, z1 - z0])
    m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return m


def cy(r, h, z0=0.0, sections=48):
    m = tcyl(radius=r, height=h, sections=sections)
    m.apply_translation([0, 0, z0 + h / 2])
    return m


def an(ro, ri, h, z0=0.0, sections=64):
    m = tann(r_min=ri, r_max=ro, height=h, sections=sections)
    m.apply_translation([0, 0, z0 + h / 2])
    return m


def cat(*ms):
    return trimesh.util.concatenate([m for m in ms if m is not None])


# ------------------------------------------------------------------------------------------------ #
# stand-ins for bought parts and context (dimensions from datasheets, rounded)
# ------------------------------------------------------------------------------------------------ #

def hr100a_body():
    base = bx(-99, 99, -167, 127, 0, 80)
    pan = cat(cy(45, 2, 84.5), cy(4, 6.5, 78))
    lid = an(86, 38, 30.5, 284.5)
    col = bx(-30, 30, 100, 127, 80, 315)
    return cat(base, pan, lid, col)


def hr100a_glass():
    return an(81, 78, 198.5, 86)


def nema(size=28.2, length=32.0, shaft_d=5.0, shaft_l=20.0):
    body = bx(-size / 2, size / 2, -size / 2, size / 2, -length, 0)
    boss = cy(11.0, 1.5, 0)
    shaft = cy(shaft_d / 2, shaft_l, 0)
    return cat(body, boss, shaft)


def std_servo():
    body = bx(-30.7, 10, -10.25, 10.25, -28, 8)          # x along L; shaft at origin, up = +z
    ears = bx(-37.7, 17, -9, 9, -2.5, 0)
    spline = cy(3, 4, 8)
    horn = cy(10, 2.5, 12)
    return cat(body, ears, spline, horn)


def micro_servo():
    body = bx(-17.5, 5, -6.1, 6.1, -16, 6)
    ears = bx(-22, 9.5, -6.1, 6.1, -1, 1)
    return cat(body, ears, cy(2.4, 3, 6), bx(-2, 14, -2, 2, 9, 10.5))


def solenoid():
    return cat(bx(-15, 15, -6.5, 6.5, -5.5, 5.5), cy(2.5, 8, 0).apply_transform(T(15, 0, 0, ry=90)) or None)


def board(w, l, t=1.6):
    return bx(-w / 2, w / 2, -l / 2, l / 2, 0, t)


def cam3():
    return cat(board(25, 24), bx(-4.3, 4.3, -4.3, 4.3, 1.6, 7.0))


def hq_cam_zoom():
    return cat(board(38, 38), cy(18, 10, 1.6), cy(15, 90, 11.6), cy(17, 12, 60))


LEDC = "#efeaf8"


def led_pad(w=240, h=175, t=5):
    return bx(-w / 2, w / 2, -t / 2, t / 2, 0, h)


def grad_cyl():
    foot = trimesh.creation.cylinder(radius=P.CYL_HEX_AF / 2 / math.cos(math.pi / 6), height=8, sections=6)
    foot.apply_translation([0, 0, 4])
    return cat(foot, an(P.CYL_OD / 2, P.CYL_OD / 2 - 1.2, P.CYL_H - 8, 8))


def linear_stage(stroke=150.0):
    """DIY stage: printed motor block (z 0-20) and end block (z 220-240), two Ø8 x 200 rods, a NEMA 17
    with an integrated lead screw under the motor block. Axis +z, rods at x = +-25."""
    mb = stl("stage_motor_block").copy()
    eb = stl("stage_end_block").copy(); eb.apply_translation([0, 0, 220])
    r1 = cy(4, 200, 20); r1.apply_translation([-P.STAGE_ROD_X, 0, 0])
    r2 = cy(4, 200, 20); r2.apply_translation([P.STAGE_ROD_X, 0, 0])
    screw = cy(4, 225, 0)
    motor = nema(42.3, 40, 5, 0); motor.apply_transform(T())
    return cat(mb, eb, r1, r2, screw, motor)


def stage_slider():
    m = stl("stage_carriage").copy()
    m.apply_translation([0, 0, -15])
    return m


def load_cell():
    return bx(0, 34, -3.2, 3.2, -3.2, 3.2)


def powder_cone(r, angle_deg, z0=0.0):
    h = r * math.tan(math.radians(angle_deg))
    m = trimesh.creation.cone(radius=r, height=h, sections=64)
    m.apply_translation([0, 0, z0])
    return m


@lru_cache(maxsize=None)
def auger_mesh():
    m = trimesh.load(DOSER / "STL/parts/auger.stl", force="mesh")
    return m


@lru_cache(maxsize=None)
def doser_module():
    """PR #176's servos-above assembly (GLB, metres, y up) without the auger and its cap, in mm, z up,
    with the auger axis along +y through (0, 0, 38.25) and the outlet face at y = 35.4."""
    s = trimesh.load(DOSER / "GLB/assembly_servos_above.glb")
    keep = []
    R = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1.0]])
    for name in s.graph.nodes_geometry:
        M, g = s.graph[name]
        if g in ("GLTF_41", "GLTF_18"):        # auger, auger cap
            continue
        m = s.geometry[g].copy()
        m.apply_transform(M)
        m.apply_scale(1000.0)
        m.apply_transform(R)
        e = m.bounds[1] - m.bounds[0]
        if max(e) < 8:
            continue
        keep.append(m)
    return cat(*keep)


def auger_at(outlet_xyz, tilt_deg, azim_deg=0.0):
    """The auger (outlet face at z = 0 in its STL, axis +z) with its outlet at outlet_xyz, tilted
    outlet-down by tilt_deg from horizontal, rising towards -y rotated by azim_deg about z."""
    m = auger_mesh().copy()
    lo, hi = m.bounds
    m.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    # axis +z (outlet at z=0, cap at z=250) -> pointing up and back at (90 - tilt) from vertical
    m.apply_transform(T(rx=-(90 - tilt_deg)))
    m.apply_transform(T(rz=azim_deg))
    m.apply_translation(outlet_xyz)
    return m


# ------------------------------------------------------------------------------------------------ #
# the ten assemblies
# ------------------------------------------------------------------------------------------------ #
PAN_TOP = 86.5
FLOOR = 80.0
ADAPTER_Z = PAN_TOP           # pan adapter's frame origin
RISER_Z = PAN_TOP + 11.0      # top of the adapter boss


def balance(comps, step=0):
    comps.append(Comp("A&D HR-100A balance (existing)", hr100a_body(), "#e6e6e6", T(), step, (0, 0, 0), "context"))
    comps.append(Comp("breeze break", hr100a_glass(), GLASS, T(), step, (0, 0, 0), "context", 0.18))


def tripod(comps, leg, step_legs, step_spider):
    z_sp = FLOOR + leg
    for k in range(3):
        a = 90 + 120 * k
        x, y = P.TRIPOD_R * math.cos(math.radians(a)), P.TRIPOD_R * math.sin(math.radians(a))
        comps.append(Comp(f"tripod leg {leg} mm", stl(f"tripod_leg_{leg}"), PRINTED, T(x, y, FLOOR), step_legs,
                          (0, 0, 80)))
    comps.append(Comp("tripod spider", stl("tripod_spider"), PRINTED, T(0, 0, z_sp), step_spider, (0, 0, 90)))
    return z_sp + 6.0


def a1_heap():
    c: list[Comp] = []
    balance(c)
    c.append(Comp("pan adapter", stl("pan_adapter"), PRINTED, T(0, 0, ADAPTER_Z), 1, (0, 0, 120)))
    c.append(Comp("riser 160 mm", stl("riser_160"), PRINTED, T(0, 0, RISER_Z), 2, (0, 0, 140)))
    top = tripod(c, 160, 3, 4)
    c.append(Comp("overflow tray", stl("overflow_tray"), PRINTED, T(0, 0, top), 5, (0, 0, 80)))
    z_ped = RISER_Z + 160
    c.append(Comp("pedestal Ø20", stl("pedestal_d20"), PRINTED, T(0, 0, z_ped), 6, (0, 0, 60), group="pedestal"))
    c.append(Comp("camera on retort-stand clamp", cat(stl("camera_rod_clamp"), cam3().apply_transform(T(0, -63, 14, rx=90)) or cam3()),
                  PRINTED, T(0, -125, z_ped - 14, rz=0), 7, (0, -80, 0)))
    c.append(Comp("Camera Module 3", cam3(), BOUGHT, T(0, -189, z_ped + 2, rx=90), 7, (0, -80, 0), "bought"))
    c.append(Comp("retort stand rod", cy(6, 330), METAL, T(0, -125, 0), 7, (0, -80, 0), "bought"))
    c.append(Comp("LED backlight pad", led_pad(), LEDC, T(0, 140, z_ped - 90), 8, (0, 80, 0), "bought"))
    c.append(Comp("doser auger (45°)", auger_at((0, 0, z_ped + 4 + 12), 45), DOSERC, T(), 9, (0, 60, 60), "context",
                  group="auger"))
    return {"title": "1. Heap angle of repose", "comps": c, "steps": [
        "The HR-100A as it is: pan Ø90, breeze break Ø156",
        "Pan adapter on the pan; centre it by eye (2 mm ring all round)",
        "160 mm riser pushes into the adapter's socket",
        "Three 160 mm tripod legs stand on the chamber floor, clear of the pan",
        "Tripod spider on the legs",
        "Overflow tray on the spider; the riser passes its chimney untouched",
        "Ø20 pedestal (powder glued on top) on the riser",
        "Camera level with the pedestal, outside the glass",
        "LED pad behind: the heap shows as a silhouette",
        "Doser at 45°, outlet 12 mm above the pedestal"],
        "view": {"azimuth": -35, "elevation": 18, "focus": (0, 0, z_ped), "zoom": 1.35}}


def a2_density():
    c: list[Comp] = []
    z0 = P.TAP_BASE_T
    c.append(Comp("tapper base", stl("tapper_base"), PRINTED, T(), 0, (0, 0, 0)))
    c.append(Comp("anvil, 304 SS Ø25.4 x 6.35", cy(12.7, P.ANVIL_T, P.ANVIL_TOP - P.ANVIL_T), STEEL, T(), 1, (0, 0, 50), "bought"))
    for x in (-P.TAP_ROD_X, P.TAP_ROD_X):
        c.append(Comp("guide rod Ø6 x 100", cy(3, 100, z0 - 1), STEEL, T(x, 0, 0), 2, (0, 0, 140), "bought"))
    c.append(Comp("NEMA 11 stepper", nema(28.2, 32, 5, 20), BOUGHT, T(0, 38, P.TAP_SHAFT_Z, rx=90), 3, (0, 80, 0), "bought"))
    c.append(Comp("snail cam (2 lobes, 3 mm drop)", stl("tapper_cam"), PRINTED, T(0, 28, P.TAP_SHAFT_Z, rx=90), 4,
                  (0, 0, 60), group="cam"))
    c.append(Comp("carriage", stl("tapper_carriage"), PRINTED, T(), 5, (0, 0, 120), group="carriage"))
    c.append(Comp("10 mL Class A cylinder", grad_cyl(), GLASS, T(0, 0, P.ANVIL_TOP + 5), 6, (0, 0, 150), "bought", 0.45,
                  group="carriage"))
    c.append(Comp("powder column", cy(P.CYL_OD / 2 - 1.3, 60, 0), "#d9c9a3", T(0, 0, P.ANVIL_TOP + 5 + 8), 6, (0, 0, 150),
                  "context", group="powder"))
    c.append(Comp("camera tower", stl("camera_tower"), PRINTED, T(0, -150, 0), 7, (0, -60, 0)))
    c.append(Comp("camera carriage + Camera Module 3", stl("camera_carriage"), PRINTED, T(0, -150, 40, rz=0), 7, (0, -60, 0)))
    c.append(Comp("Camera Module 3", cam3(), BOUGHT, T(0, -163.5, 54, rx=90), 7, (0, -60, 0), "bought"))
    c.append(Comp("LED backlight pad", led_pad(), LEDC, T(0, 110, 0), 8, (0, 60, 0), "bought"))
    return {"title": "2. Bulk and tapped density", "comps": c, "steps": [
        "Printed base: rod bosses, anvil pocket, motor plate",
        "Glue the 1/4 in 304 stainless anvil disc in its pocket (1 mm proud)",
        "Press the two Ø6 mm rods into the bosses",
        "Bolt the NEMA 11 to the motor plate (4 x M2.5)",
        "Two-lobe snail cam on the shaft, set screw on the flat",
        "Slide the carriage down the rods; its lug rests over the cam",
        "Cylinder foot into the carriage pocket, tube through the collar",
        "Camera at the column, 120 mm away",
        "Backlight behind: column height to about 0.05 mm"],
        "view": {"azimuth": -50, "elevation": 20, "focus": (0, 0, 60), "zoom": 1.2}}


def a3_tilt():
    c: list[Comp] = []
    hz = P.HINGE_Z
    c.append(Comp("tilt base", stl("tilt_base"), PRINTED, T(), 0, (0, 0, 0)))
    sz = hz - P.CENTRE_D
    c.append(Comp("15.5 kg·cm metal-gear servo (FS5115M)", std_servo(), BOUGHT, T(29, -10.35 + 10.35, sz, ry=90).dot(T()) , 1,
                  (60, 0, 0), "bought"))
    c.append(Comp("15T pinion on the horn", stl("tilt_pinion_15t"), PRINTED, T(43.5, 0, sz, ry=90), 2, (40, 0, 0),
                  group="pinion"))
    c.append(Comp("tilt plate", stl("tilt_plate"), PRINTED, T(), 3, (0, 0, 80), group="plate"))
    c.append(Comp("hinge pin Ø5", cy(2.5, 92).apply_transform(T(ry=90)) or cy(2.5, 92), STEEL, T(-46, 0, hz, ry=90), 4,
                  (-80, 0, 0), "bought", group="plate"))
    c.append(Comp("30T gear on the plate lug", stl("tilt_gear_30t"), PRINTED, T(43.5, 0, hz, ry=90), 5, (40, 0, 0),
                  group="plate"))
    c.append(Comp("LSM6DSOX IMU", board(25.4, 17.8), BOUGHT, T(0, 60, P.PLATE_Z0 - 2 - 1.6), 6, (0, 0, -40),
                  "bought", group="plate"))
    c.append(Comp("304 stainless coupon 100 x 50 x 1", bx(-25, 25, 14.1, 114.1, 0, 1.0), STEEL,
                  T(0, 0, P.PLATE_TOP - 0.8), 7, (0, 0, 60), "bought", group="plate"))
    c.append(Comp("ring (Ø25 ID) filled with powder", stl("wall_ring"), PRINTED, T(0, 80, P.PLATE_TOP + 0.2 + 0.5), 8,
                  (0, 0, 60), group="ring"))
    c.append(Comp("powder in the ring", cy(12.4, 5.6, 0), "#d9c9a3", T(0, 80, P.PLATE_TOP + 0.2), 8, (0, 0, 60),
                  "context", group="ring"))
    c.append(Comp("lid with washers (sets the stress)", stl("ring_lid"), PRINTED, T(0, 80, P.PLATE_TOP + 6.0), 9,
                  (0, 0, 60), group="ring"))
    return {"title": "3. Tilting plate: wall friction and layer start angle", "comps": c, "steps": [
        "Printed base with hinge towers and servo bracket",
        "Servo through the bracket window, 4 x M2.5",
        "15T m1.5 pinion screwed to the servo horn",
        "Plate between the towers",
        "Ø5 mm steel hinge pin through towers and lugs",
        "30T gear on the plate's lug: servo 180° = table 90°",
        "IMU under the plate reads the true angle",
        "Coupon (PLA, 304 SS or glass) in the pocket",
        "Ring on 0.5 mm feeler-gauge shims, filled and struck off; shims out",
        "Lid with washers: 70-450 Pa on the powder"],
        "view": {"azimuth": -40, "elevation": 24, "focus": (0, 50, 60), "zoom": 1.25}}


def a4_psd():
    c: list[Comp] = []
    c.append(Comp("LED backlight pad (flat)", bx(-120, 120, -87, 87, -5, 0), LEDC, T(), 0, (0, 0, 0), "bought"))
    c.append(Comp("microscope base", stl("micro_base"), PRINTED, T(), 1, (0, 0, 60)))
    c.append(Comp("column", stl("micro_column"), PRINTED, T(0, 42, 6), 2, (0, 0, 120)))
    c.append(Comp("mechanical X-Y stage", cat(bx(-50, 50, -35, 25, 6, 14), bx(-40, 40, -10, 10, 14, 18)), METAL,
                  T(), 3, (0, -60, 0), "bought"))
    c.append(Comp("glass slide with grains", bx(-37.5, 37.5, -12.5, 12.5, 18, 19), GLASS, T(), 4, (0, -40, 30), "bought", 0.6))
    c.append(Comp("camera carriage", stl("micro_carriage"), PRINTED, T(0, 42, 100), 5, (0, 0, 80)))
    c.append(Comp("Arducam IMX477 HQ camera + 0.12-1.8x zoom lens", hq_cam_zoom(), BOUGHT, T(0, -3, 127, rx=180), 6, (0, 0, 120), "bought"))
    return {"title": "4. PSD and shape from images", "comps": c, "steps": [
        "LED pad flat on the bench",
        "Printed base over the pad; window over the light",
        "Column into the base socket",
        "Mechanical X-Y stage bolted to the base",
        "Slide with a sparse layer of grains",
        "Camera carriage on the column, thumb screw",
        "IMX477 HQ camera + zoom lens, looking down; focus with the carriage"],
        "view": {"azimuth": -45, "elevation": 22, "focus": (0, 0, 70), "zoom": 1.3}}


def a5_orifice():
    c: list[Comp] = []
    balance(c)
    c.append(Comp("catch cup", stl("catch_cup"), PRINTED, T(0, 0, PAN_TOP), 1, (0, 0, 120), group="catch"))
    top = tripod(c, 120, 2, 3)
    c.append(Comp("cup holder", stl("cup_holder"), PRINTED, T(-74, 0, top, rz=0), 4, (0, 0, 80)))
    zc = top + 10
    c.append(Comp("gate guide", stl("gate_guide"), PRINTED, T(0, 0, zc), 5, (0, 0, 60)))
    c.append(Comp("gate slide", stl("gate_slide"), "#e76f51", T(0, 0, zc + 4.4), 5, (0, 0, 60), group="gate"))
    c.append(Comp("9 g micro servo", micro_servo(), BOUGHT, T(38, -14, zc + 6 + 16), 6, (40, 0, 0), "bought"))
    c.append(Comp("orifice disc", stl("orifice_disc_3p00"), PRINTED, T(0, 0, zc + 6), 7, (0, 0, 60)))
    c.append(Comp("orifice cup", stl("orifice_cup"), PRINTED, T(0, 0, zc + 8), 8, (0, 0, 80)))
    c.append(Comp("JF-0530B solenoid tapper", bx(-15, 15, -6.5, 6.5, -5.5, 5.5), BOUGHT, T(-74 + 76, 32, top + 13), 9,
                  (0, 60, 0), "bought"))
    c.append(Comp("doser auger (45°)", auger_at((0, 0, zc + 8 + 46 + 10), 45), DOSERC, T(), 10, (0, 60, 60), "context"))
    return {"title": "5. Orifice cup", "comps": c, "steps": [
        "The HR-100A",
        "Catch cup on the pan: the balance weighs only what flows",
        "Tripod legs (120 mm) on the chamber floor",
        "Spider on the legs",
        "Cup holder on the spider",
        "Gate guide with the sliding gate",
        "9 g servo moves the gate 10 mm",
        "Orifice disc (1-6 mm) under the cup",
        "Cup screwed down: disc clamped flat",
        "Second solenoid on the holder taps the cup",
        "Doser fills the cup to 5 g with the gate shut"],
        "view": {"azimuth": -35, "elevation": 22, "focus": (0, 0, 200), "zoom": 0.75}}


def a6_humidity():
    c: list[Comp] = []
    c.append(Comp("airtight box 1.2 L", cat(bx(-95, 95, -65, 65, 0, 2), an(1, 0, 0.1) or bx(-95, -93, -65, 65, 0, 95),
                                          bx(93, 95, -65, 65, 0, 95), bx(-95, 95, -65, -63, 0, 95), bx(-95, 95, 63, 65, 0, 95)),
                  GLASS, T(), 0, (0, 0, 0), "bought", 0.25))
    c.append(Comp("slurry tray (saturated salt)", stl("hc_slurry_tray"), PRINTED, T(0, 0, 2), 1, (0, 0, 100)))
    c.append(Comp("saturated salt slurry", bx(-68, 68, -33, 33, 3.6, 12), "#f1f1f1", T(0, 0, 0), 2, (0, 0, 100), "context"))
    c.append(Comp("perforated shelf", stl("hc_shelf"), PRINTED, T(0, 0, 2 + 30), 3, (0, 0, 100)))
    c.append(Comp("sample dish Ø80, layer under 1 mm", stl("hc_sample_dish"), PRINTED, T(-20, 0, 34.4), 4, (0, 0, 80)))
    c.append(Comp("powder layer", cy(38.5, 0.8, 0), "#d9c9a3", T(-20, 0, 35.6), 4, (0, 0, 80), "context"))
    c.append(Comp("SHT45 sensor on its clip", cat(stl("hc_sensor_clip"), board(25.4, 17.8).apply_translation([0, 0, 2]) or board(25.4, 17.8)),
                  PRINTED, T(45, 0, 34.4), 5, (0, 0, 80)))
    c.append(Comp("25 mm 5 V fan on its mount", cat(stl("hc_fan_mount"), bx(-12.5, 12.5, -12.5, 12.5, 3, 13)), PRINTED,
                  T(55, 35, 60, rx=90), 6, (0, 0, 80)))
    c.append(Comp("lid with PG7 cable gland", cat(bx(-97, 97, -67, 67, 95, 100), cy(6, 12, 100).apply_translation([60, 0, 0]) or cy(6, 12, 100)),
                  GLASS, T(), 7, (0, 0, 60), "bought", 0.35))
    return {"title": "6. Humidity chambers (x6)", "comps": c, "steps": [
        "Clear airtight box, about 1.2 L",
        "Slurry tray on the floor",
        "Saturated slurry: MgCl2, Mg(NO3)2, NaNO3, NaCl or KCl; or silica gel",
        "Perforated shelf 30 mm above the slurry",
        "Ø80 dish: about 3 g in a layer under 1 mm",
        "SHT45 on its clip next to the sample",
        "25 mm fan mixes the air (10-50x faster equilibration)",
        "Lid on; the sensor cable leaves through a PG7 gland"],
        "view": {"azimuth": -40, "elevation": 30, "focus": (0, 0, 40), "zoom": 1.25}}


def a7_drum():
    c: list[Comp] = []
    c.append(Comp("doser module (existing, auger removed)", doser_module(), DOSERC, T(), 0, (0, 0, 0), "context"))
    # drum shaft frame: z=0 at the flange, axis -> doser +y (towards the cap end), axis at z = 38.25
    M = T(0, 0, 0, rx=-90).copy()
    M[:3, 3] = [0, 35.4 - P.DRUM_EXT, 38.25]
    c.append(Comp("drum shaft (replaces the auger)", stl("drum_shaft"), PRINTED, M, 1, (0, 260, 0), group="drum"))
    Md = M @ T(0, 0, 0, rx=180)
    c.append(Comp("drum body, 24 ribs", stl("drum_body"), PRINTED, Md, 2, (0, -80, 0), group="drum"))
    c.append(Comp("rear-wall disc (black)", cy(19, 1.2).apply_translation([0, 0, 3]) or cy(19, 1.2), DARK, Md, 3, (0, -80, 0), group="drum"))
    c.append(Comp("powder, 40 % fill", trimesh.creation.cylinder(radius=19.5, height=14, sections=64).slice_plane([0, -4, 0], [0, -1, 0]) if False else cy(1, 1), "#d9c9a3", Md, 4, (0, -80, 0), "context", 0.0, group="drum"))
    c.append(Comp("acrylic window Ø50 x 2", cy(25, 2, 3 + P.DRUM_DEPTH + 1), GLASS, Md, 5, (0, -80, 0), "bought", 0.35, group="drum"))
    c.append(Comp("bezel, 3 x M3", stl("drum_bezel"), PRINTED, Md @ T(0, 0, 3 + P.DRUM_DEPTH + 3), 6, (0, -80, 0), group="drum"))
    return {"title": "7. Rotating drum on the doser's stepper", "comps": c, "steps": [
        "The doser with its auger taken out of the brackets",
        "Drum shaft in the brackets: same tube, 44T gear at the auger's place",
        "Drum body on the shaft flange, 3 x M3 into heat-set inserts",
        "Black (or white) rear-wall disc for contrast",
        "Fill 40 % (about 7.5 mL)",
        "Acrylic window over the open face",
        "Bezel, 3 x M3: the camera looks along the axis"],
        "view": {"azimuth": -55, "elevation": 22, "focus": (0, 40, 30), "zoom": 0.8}}


def a8_ucs():
    c: list[Comp] = []
    c.append(Comp("UCS base and column", stl("ucs_base"), PRINTED, T(), 0, (0, 0, 0)))
    c.append(Comp("100 g load cell (TAL221)", load_cell(), METAL, T(-48 + 10, 0, 8 + 20 + 3.2), 1, (0, 0, 60), "bought"))
    c.append(Comp("sample base", stl("ucs_sample_base"), PRINTED, T(-38 + 34 - 6, 0, 8 + 20 + 6.4), 2, (0, 0, 60), group="sample"))
    zb = 8 + 20 + 6.4 + 4
    c.append(Comp("split mould half A", stl("split_mould_A"), PRINTED, T(-10, 0, zb), 3, (0, 60, 0), group="mouldA"))
    c.append(Comp("split mould half B", stl("split_mould_B"), PRINTED, T(-10, 0, zb), 3, (0, -60, 0), group="mouldB"))
    c.append(Comp("2 latch rings", cat(stl("mould_ring").copy().apply_translation([0, 0, 6]) or stl("mould_ring"),
                                       stl("mould_ring").copy().apply_translation([0, 0, 28]) or stl("mould_ring")),
                  PRINTED, T(-10, 0, zb), 4, (0, 0, 80), group="rings"))
    c.append(Comp("piston + slotted weights", cat(stl("ucs_piston"), cy(20, 6, 23), cy(20, 6, 29.5)), PRINTED,
                  T(-10, 0, zb + 40 - 7), 5, (0, 0, 80), group="piston"))
    c.append(Comp("DIY lead-screw stage (vertical)", linear_stage(), METAL, T(-10, 35, 50), 6, (0, 80, 0), "bought"))
    c.append(Comp("stage carriage", stage_slider(), PRINTED, T(-10, 35, zb + 54), 6, (0, 80, 0), group="platen"))
    c.append(Comp("platen arm", stl("ucs_platen"), PRINTED, T(-10, 0, zb + 50, rz=90), 7, (0, 0, 60), group="platen"))
    return {"title": "8. Unconfined strength", "comps": c, "steps": [
        "Printed base with the load-cell block and stage column",
        "100 g bar load cell, cantilevered",
        "Sample base on the load cell's free end",
        "Two mould halves (Ø20 x 40) on dowels",
        "Two latch rings hold the mould shut",
        "Fill by doser; piston + weights: 0.2-2 kPa",
        "DIY lead-screw stage on the column",
        "Platen arm on the slider; lower at 0.1 mm/s after the mould opens"],
        "view": {"azimuth": -50, "elevation": 20, "focus": (0, 20, 70), "zoom": 1.2}}


def a9_spread():
    c: list[Comp] = []
    st = linear_stage()
    Ms = T(0, 0, 30, ry=90) @ T(rz=-90)
    c.append(Comp("DIY lead-screw stage (horizontal)", st, METAL, Ms, 0, (0, 0, 0), "bought"))
    c.append(Comp("stage carriage", stage_slider(), PRINTED, T(60, 0, 0) @ Ms @ T(0, 0, 0), 4, (0, 0, 60), group="blade"))
    c.append(Comp("2 brackets", cat(stl("spread_bracket").copy().apply_transform(T(70, 52, 0)),
                                    stl("spread_bracket").copy().apply_transform(T(190, 52, 0))),
                  PRINTED, T(), 1, (0, 60, 0)))
    zb = 31.0 - 0.15 - 10.0          # bed bottom: coupon top 0.15 mm under the blade edge (z = 31)
    c.append(Comp("coupon bed", stl("coupon_bed"), PRINTED, T(130, 88, zb), 2, (0, 60, 40)))
    c.append(Comp("304 stainless coupon 100 x 30 x 0.91", bx(-50, 50, -15, 15, 0, 0.91), STEEL, T(130, 88, zb + 10 - 0.91), 3, (0, 0, 60), "bought"))
    c.append(Comp("blade carriage", stl("blade_carriage"), PRINTED, T(60, 0, 52), 4, (0, 0, 60), group="blade"))
    c.append(Comp("blade, 304 SS 1.5 x 25 x 52", bx(-26, 26, -0.75, 0.75, 0, 25), STEEL, T(60, 88, 31.0), 5, (0, 0, 60),
                  "bought", group="blade"))
    c.append(Comp("powder line", bx(-1.5, 1.5, -14, 14, 0, 1.2), "#d9c9a3",
                  T(84, 88, zb + 10), 6, (0, 0, 40), "context", group="powder"))
    return {"title": "9. Blade spreading", "comps": c, "steps": [
        "DIY stage: NEMA 17 lead screw, two Ø8 rods, 4 x LM8UU",
        "Two printed brackets tie the coupon bed to the stage",
        "Coupon bed, parallel to the travel",
        "Coupon (304 SS or PLA), flush with the bed",
        "Blade carriage on the slider",
        "Blade clamped at a 0.10-0.20 mm gap (feeler gauges)",
        "Doser lays a 0.2-0.5 g line; the blade spreads it"],
        "view": {"azimuth": -50, "elevation": 30, "focus": (100, 40, 30), "zoom": 1.15}}


def a10_faraday():
    c: list[Comp] = []
    balance(c)
    top = tripod(c, 120, 1, 2)
    c.append(Comp("can cradle", stl("fc_cradle"), PRINTED, T(0, 0, top), 3, (0, 0, 80)))
    zc = top + 4
    c.append(Comp("outer can (grounded shield)", cat(cy(35.5, 1.0, 0), an(35.5, 34.8, 80, 0)), METAL, T(0, 0, zc), 4, (0, 0, 120), "bought"))
    c.append(Comp("insulator base", stl("fc_insulator_base"), PRINTED, T(0, 0, zc + 1), 5, (0, 0, 100)))
    c.append(Comp("3 PTFE standoffs", cat(*[cy(2.5, 10, 0).apply_translation([12 * math.cos(math.radians(a)), 12 * math.sin(math.radians(a)), 0]) or cy(2.5, 10) for a in (90, 210, 330)]),
                  "#f4f4f4", T(0, 0, zc + 4), 6, (0, 0, 100), "bought"))
    c.append(Comp("inner cup (aluminium)", cat(cy(20, 1.0, 0), an(20, 19.3, 50, 0)), STEEL, T(0, 0, zc + 14), 7, (0, 0, 120), "bought",
                  group="inner"))
    c.append(Comp("lid with inlet funnel", stl("fc_lid"), PRINTED, T(0, 0, zc + 80), 8, (0, 0, 80)))
    c.append(Comp("FC-1 charge amplifier in its box", cat(stl("fc_pcb_box"), board(50, 40).apply_translation([0, 0, 8]) or board(50, 40)),
                  PRINTED, T(95, 0, 0), 9, (60, 0, 0)))
    c.append(Comp("doser auger (45°)", auger_at((0, 0, zc + 80 + 15), 45), DOSERC, T(), 10, (0, 60, 60), "context"))
    return {"title": "10. Faraday cup", "comps": c, "steps": [
        "The HR-100A (the cup is not weighed during dosing)",
        "Tripod legs on the chamber floor",
        "Spider on the legs",
        "Can cradle on the spider",
        "Grounded aluminium outer can",
        "Printed insulator base",
        "Three PTFE standoffs",
        "Inner aluminium cup on the standoffs; BNC lead to the cup",
        "Lid with the inlet funnel (aluminium tape inside: shield)",
        "FC-1 charge amplifier beside the balance",
        "Doser outlet over the funnel"],
        "view": {"azimuth": -35, "elevation": 22, "focus": (0, 0, 220), "zoom": 0.75}}


ASSEMBLIES = {
    "t01_heap": a1_heap, "t02_density": a2_density, "t03_tilt": a3_tilt, "t04_psd": a4_psd,
    "t05_orifice": a5_orifice, "t06_humidity": a6_humidity, "t07_drum": a7_drum, "t08_ucs": a8_ucs,
    "t09_spread": a9_spread, "t10_faraday": a10_faraday,
}


def set_view(pl, a, dist=None):
    v = a["view"]
    if dist is None:
        b = np.array([c.mesh.bounds @ c.M[:3, :3].T + c.M[:3, 3] for c in a["comps"] if c.kind != "context"])
        diag = float(np.linalg.norm(b.reshape(-1, 3).max(0) - b.reshape(-1, 3).min(0)))
        dist = 1.7 * diag / v.get("zoom", 1.0)
    az, el = math.radians(v["azimuth"] - 90), math.radians(v["elevation"])
    f = np.array(v["focus"], float)
    pos = f + dist * np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    pl.camera.position = tuple(pos)
    pl.camera.focal_point = tuple(f)
    pl.camera.up = (0, 0, 1)
    pl.camera.view_angle = 30


def render_still(key: str, path: Path, size=(1600, 1200)):
    import pyvista as pv
    pv.OFF_SCREEN = True
    a = ASSEMBLIES[key]()
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("white")
    for comp in a["comps"]:
        if comp.opacity <= 0:
            continue
        m = comp.mesh.copy()
        m.apply_transform(comp.M)
        pl.add_mesh(pv.wrap(m), color=comp.color, opacity=comp.opacity, smooth_shading=False,
                    specular=0.2 if comp.kind != "context" else 0.0)
    set_view(pl, a)
    pl.add_text(a["title"], font_size=14, color="black", position="upper_left")
    pl.screenshot(str(path))
    pl.close()


if __name__ == "__main__":
    import sys
    out = HERE / "out" / "renders"
    out.mkdir(parents=True, exist_ok=True)
    for k in (sys.argv[1:] or list(ASSEMBLIES)):
        try:
            render_still(k, out / f"{k}.png")
            print("rendered", k, flush=True)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            print("FAILED", k, exc, flush=True)
