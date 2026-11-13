"""Where each screw, nut and bolt goes on the current doser (the #193 Onshape assembly).

    python assembly_193.py fetch                 # once: assembly definition + part STLs (read-only)
    xvfb-run -a python hardware_193.py render    # writes ../assembly/doser_193_hardware.png

#193 doesn't model fasteners, so each one here is placed on a hole axis read from the
assembly: the 52 mates give most of them, and the rest (the servo-post holes, the
tap-collar clamp, the back stand bracket's second bolt) were found by sectioning the
parts. The joint table in ../assembly/README.md lists the same joints; the sizes are
the ones in ../inventory-checklist.csv. The fasteners are drawn to the ISO head sizes
(socket head ISO 4762, button head ISO 7380, flat head ISO 10642, nylon-insert locknut
DIN 985), pulled out along their hole axes, with a dashed line through the hole.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE.parent / "assembly"

# ---- fastener geometry (mm) --------------------------------------------------------------
# kind: (head, d, length, head dia, head height, hex key / socket, thread pitch)
SCREWS = {
    "M3x14 SHCS": ("socket", 3.0, 14, 5.5, 3.0, 2.5, 0.5),
    "M3x10 SHCS": ("socket", 3.0, 10, 5.5, 3.0, 2.5, 0.5),
    "M3x5 SHCS": ("socket", 3.0, 5, 5.5, 3.0, 2.5, 0.5),
    "M2.5x8 SHCS": ("socket", 2.5, 8, 4.5, 2.5, 2.0, 0.45),
    "M3x20 BHCS": ("button", 3.0, 20, 5.7, 1.65, 2.0, 0.5),
    "M3x25 BHCS": ("button", 3.0, 25, 5.7, 1.65, 2.0, 0.5),
    "M3x30 FHCS": ("flat", 3.0, 30, 6.0, 1.5, 2.0, 0.5),
    "M5x40 BHCS": ("button", 5.0, 40, 9.5, 2.75, 3.0, 0.8),
    "stand bolt": ("hex", 6.0, 25, 10.0, 4.0, 0.0, 1.0),
}
NUTS = {  # across flats, height, nylon insert?
    "M3 locknut": (5.5, 4.0, True),
    "M5 locknut": (8.0, 5.0, True),
    "stand nut": (10.0, 5.2, False),
}
STEEL, SOCKET, NUT, NYLON = "#3c4148", "#121417", "#5d646d", "#e9e2c8"


def _revolve(profile):
    import trimesh
    return trimesh.creation.revolve(np.asarray(profile, float), sections=48)


def screw_meshes(kind):
    """Meshes in a local frame: the shank runs down -z from the seat (z = 0) to z = -L; the head is above.
    For the flat head, z = 0 is the top of the head (flush with the countersunk face)."""
    import trimesh
    head, d, L, dk, k, s, p = SCREWS[kind]
    r, rm = d / 2, d / 2 - 0.55 * p
    z_top_thread = -(dk - d) / 2 if head == "flat" else 0.0
    prof = [(0, -L), (rm, -L), (r, -L + 0.4 * p)]
    z = -L + p
    while z < z_top_thread - 0.6 * p:
        prof += [(rm, z), (r, z + 0.5 * p)]
        z += p
    prof += [(r, z_top_thread)]
    if head == "socket":
        prof += [(dk / 2, 0), (dk / 2, k - 0.3), (dk / 2 - 0.3, k), (0, k)]
        top = k
    elif head == "button":
        prof += [(dk / 2, 0), (dk / 2, 0.22 * k)]
        for a in np.linspace(0, np.pi / 2, 9)[1:]:
            rr = dk / 2 * np.cos(a)
            if rr < 0.3 * dk:
                break
            prof.append((rr, 0.22 * k + 0.78 * k * np.sin(a)))
        prof += [(0.3 * dk, k), (0, k)]
        top = k
    elif head == "flat":
        prof += [(dk / 2, -0.15), (dk / 2, 0), (0, 0)]
        top = 0.0
    else:  # hex bolt: shank only, the hex head is added below
        prof += [(0, 0)]
        top = k
    body = _revolve(prof)
    parts = [(body, STEEL)]
    if head == "hex":
        hx = trimesh.creation.cylinder(radius=dk / 2 / np.cos(np.pi / 6), height=k, sections=6)
        hx.apply_translation([0, 0, k / 2])
        parts.append((hx, STEEL))
    if s:
        sk = trimesh.creation.cylinder(radius=s / 2 / np.cos(np.pi / 6), height=0.12, sections=6)
        sk.apply_translation([0, 0, top + 0.02])
        parts.append((sk, SOCKET))
    return parts, top


def nut_meshes(kind):
    """Local frame: bearing face at z = 0, the nut runs up +z (away from the part)."""
    import trimesh
    s, m, nylon = NUTS[kind]
    R = s / 2 / np.cos(np.pi / 6)
    hm = m * (0.72 if nylon else 1.0)
    hx = trimesh.creation.cylinder(radius=R, height=hm, sections=6)
    hx.apply_translation([0, 0, hm / 2])
    parts = [(hx, NUT)]
    if nylon:
        ring = trimesh.creation.cylinder(radius=0.46 * s, height=m - hm, sections=40)
        ring.apply_translation([0, 0, hm + (m - hm) / 2])
        parts.append((ring, NYLON))
    hole = trimesh.creation.cylinder(radius=0.42 * s * 0.62, height=m + 0.1, sections=32)
    hole.apply_translation([0, 0, m / 2])
    parts.append((hole, SOCKET))
    return parts


def place(meshes, origin, zdir):
    import trimesh
    T = trimesh.geometry.align_vectors([0, 0, 1], np.asarray(zdir, float))
    T[:3, 3] = origin
    out = []
    for m, c in meshes:
        m = m.copy()
        m.apply_transform(T)
        out.append((m, c))
    return out


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


# ---- every fastener on the doser ----------------------------------------------------------
# Upright frame (as in assembly_193.py): +z up, +y towards the auger's outlet (front), +x right.
# seat: where the head bears (for the flat head, its top); d: into the hole; nut_at: far face of the stack.
PLATE_DOWN = unit([0, -0.0307, -1])        # the plate is tilted 1.76 deg in the assembly
COLLAR_CLAMP = unit([-0.649, 0, 0.760])
CLAMP_P0 = np.array([9.03, 1.64, 40.61])


def joints():
    J = []

    def add(group, kind, seat, d, nut=None, nut_at=None, e_s=None, e_n=6.0):
        J.append(dict(group=group, kind=kind, seat=np.array(seat, float), d=unit(d), nut=nut,
                      nut_at=None if nut_at is None else np.array(nut_at, float), e_s=e_s, e_n=e_n))

    # Servos: 4 per servo, through the servo's ear into the Base's post (4.0 mm holes), locknut behind the post.
    for y in (45.22, 93.07):
        for z in (5.10, 15.28):
            add("servo", "M3x14 SHCS", [47.75, y, z], [1, 0, 0], "M3 locknut", [55.5, y, z], e_s=17)
            add("servo", "M3x14 SHCS", [-80.5, y, z], [-1, 0, 0], "M3 locknut", [-88.25, y, z], e_s=17)
    # Servo pinions: through the 14T pinion into the servo's output shaft.
    add("pinion", "M3x10 SHCS", [25.6, 59.6, 10.2], [1, 0, 0], e_s=12)
    add("pinion", "M3x10 SHCS", [-58.25, 59.6, 10.2], [-1, 0, 0], e_s=12)
    # Hinge: 28T gear, Base tower, plate knuckle (37.75 mm). It can only go in from outside the gear: the
    # knuckles are 32.5 mm apart and the auger tube runs between them, 3.7 mm from each knuckle.
    add("hinge", "M5x40 BHCS", [37.75, 59.2, 37.4], [-1, 0, 0], "M5 locknut", [0.0, 59.2, 37.4], e_s=43, e_n=0.6)
    add("hinge", "M5x40 BHCS", [-70.25, 59.2, 37.4], [1, 0, 0], "M5 locknut", [-32.5, 59.2, 37.4], e_s=43, e_n=0.6)
    # Stepper: through the plate's 6 mm motor wall into the NEMA-11's threaded holes.
    for x in (4.3, 27.3):
        for z, yf in ((28.6, -24.5), (51.6, -24.0)):
            add("stepper", "M2.5x8 SHCS", [x, yf, z], [0, -1, 0.03], e_s=12)
    # C-clips: 2 each, through the clip's foot and the plate; locknut under the plate.
    for x in (-40.2, 7.8):
        add("clips", "M3x20 BHCS", [x, 16.0, 17.25], PLATE_DOWN, "M3 locknut", [x, 16.0, 3.5], e_s=24, e_n=7)
        add("clips", "M3x20 BHCS", [x, -65.5, 19.75], PLATE_DOWN, "M3 locknut", [x, -65.5, 6.0], e_s=24, e_n=7)
    # Tap-collar base: plain hole (button head) and countersunk hole (flat head), locknuts under the plate.
    add("tcbase", "M3x25 BHCS", [-40.2, 0.2, 23.9], PLATE_DOWN, "M3 locknut", [-40.2, 0.2, 3.9], e_s=29, e_n=7)
    add("tcbase", "M3x30 FHCS", [7.8, 0.3, 30.8], PLATE_DOWN, "M3 locknut", [7.8, 0.3, 3.9], e_s=33, e_n=7)
    # Tap collar: clamp screw across the split (two 5.6 mm ears, 2.4 mm slot), locknut on the far ear.
    add("clamp", "M3x20 BHCS", CLAMP_P0 + 8.6 * COLLAR_CLAMP, COLLAR_CLAMP, "M3 locknut", CLAMP_P0 + 22.2 * COLLAR_CLAMP,
        e_s=24, e_n=7)
    # Solenoid: from behind the collar's 1 mm flange into the solenoid frame's threaded holes.
    add("solenoid", "M3x5 SHCS", [-55.1, -6.1, 70.5], [0, 1, -0.03], e_s=9)
    add("solenoid", "M3x5 SHCS", [-30.9, -6.1, 70.3], [0, 1, -0.03], e_s=9)
    # Stand: side brackets sit on the Base (10 + 6 mm); the back bracket's rails hang under it (6 + 10 mm).
    for x in (50.8, -83.6):
        for y in (21.1, 117.1):
            add("stand_base", "stand bolt", [x, y, 10.2], [0, 0, -1], "stand nut", [x, y, -5.8], e_s=34, e_n=9)
    for x in (3.64, -36.37):
        add("stand_base", "stand bolt", [x, -50.4, 0.2], [0, 0, -1], "stand nut", [x, -50.4, -15.8], e_s=34, e_n=9)
    # Legs: through the bracket's 6.5 mm wall and the 9.5 mm leg; nut on the leg's inner face.
    for y in (44.6, 84.6):
        add("legs", "stand bolt", [115.1, y, -7.3], [-1, 0, 0], "stand nut", [99.1, y, -7.3], e_s=34, e_n=9)
        add("legs", "stand bolt", [-147.9, y, -7.3], [1, 0, 0], "stand nut", [-131.9, y, -7.3], e_s=34, e_n=9)
    for x in (3.64, -36.38):
        add("legs", "stand bolt", [x, -223.3, -23.3], [0, 1, 0], "stand nut", [x, -207.3, -23.3], e_s=34, e_n=9)
    return J


def fastener_scene(j, explode=True):
    """Meshes for one joint, plus 3D anchor points and the dashed axis segment."""
    kind, d = j["kind"], j["d"]
    L, k = SCREWS[kind][2], SCREWS[kind][4]
    e_s = j["e_s"] if explode else 0.0
    seat = j["seat"] - e_s * d
    meshes, top = screw_meshes(kind)
    out = place(meshes, seat, -d)
    head_c = seat - d * (top / 2 if top else -0.8)
    tip = seat + d * L
    anchors = {"screw": head_c}
    line_end = j["seat"] + d * L
    if j["nut"]:
        e_n = j["e_n"] if explode else 0.0
        na = j["nut_at"] + e_n * d
        out += place(nut_meshes(j["nut"]), na, d)
        anchors["nut"] = na + d * NUTS[j["nut"]][1] / 2
        line_end = na + d * (NUTS[j["nut"]][1] + 2)
    return out, anchors, (tip, line_end)


def dashes(a, b, dash=2.2, gap=1.6):
    import pyvista as pv
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = np.linalg.norm(b - a)
    if n < 1e-6:
        return None
    u = (b - a) / n
    pts, lines, t = [], [], 0.0
    while t < n:
        p0, p1 = a + u * t, a + u * min(t + dash, n)
        lines += [2, len(pts), len(pts) + 1]
        pts += [p0, p1]
        t += dash + gap
    return pv.PolyData(np.array(pts), lines=np.array(lines))


# ---- panels ------------------------------------------------------------------------------
def wash(hex_colour, f=0.42):
    c = np.array([int(hex_colour[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0
    return tuple(c + (1 - c) * f)


# title, parts shown, joint groups, (camera direction, up), focus, half-height (mm), labels
# label: (group, kind or nut, anchor "screw"/"nut", which instance (index within the group), side, bold, sub)
PANELS = [
    dict(key="servo", n="1", title="Servos and their pinions (one side; the other mirrors it)",
         parts=["Part 1 <4>", "MG-996R <2>", "MG-996R <3>", "Spur gear (14 teeth) <2>"],
         groups=["servo", "pinion"], only=lambda j: j["seat"][0] > 0,
         view=((0.42, 0.80, 0.50), (0, 0, 1)), focus=(42, 70, 10), scale=46,
         labels=[("servo", "screw", 3, "L", "M3 × 14 socket head cap screw  ×8",
                  "4 per servo: through the servo's ear\ninto the Base's post (4 mm holes)"),
                 ("servo", "nut", 2, "R", "M3 nylon-insert locknut  ×8", "on the outside of each post"),
                 ("pinion", "screw", 0, "L", "M3 × 10 socket head cap screw  ×2",
                  "through the 14T pinion into\nthe servo's output shaft")]),
    dict(key="hinge", n="2", title="Hinge (one side; the other mirrors it)",
         parts=["Part 1 <8>", "Part 1 <4>", "Spur gear (14 teeth) <2>", "Part 1 <11>"],
         groups=["hinge"], only=lambda j: j["seat"][0] >= 0,
         view=((0.50, 0.70, 0.52), (0, 0, 1)), focus=(54, 60, 30), scale=58, ghost=["Part 1 <11>"],
         labels=[("hinge", "screw", 0, "L-", "M5 × 40 button head screw  ×2",
                  "in from outside each 28T gear, through the\ngear, the Base's tower and the plate's knuckle"),
                 ("hinge", "nut", 0, "L+", "M5 nylon-insert locknut  ×2",
                  "inside each knuckle, next to the auger tube.\nCheck on doser #1: in the CAD only 2.2 mm of\n"
                  "thread comes through, and the tube is 3.7 mm away")]),
    dict(key="stepper", n="3", title="Stepper motor (fit the stepper pinion after these)",
         parts=["Part 1 <8>", "stepper_motor <1>"],
         groups=["stepper"], only=None,
         view=((0.62, 0.66, 0.42), (0, 0, 1)), focus=(36, -38, 36), scale=48,
         labels=[("stepper", "screw", 1, "R", "M2.5 × 8 socket head cap screw  ×4",
                  "through the plate's motor wall\ninto the NEMA-11's threaded holes")]),
    dict(key="plate", n="4", title="C-clips and tap-collar base on the mounting plate",
         parts=["Part 1 <8>", "Part 1 <9>", "Part 1 <10>", "tap_collar_base <1>"],
         groups=["clips", "tcbase"], only=None,
         view=((-0.55, 0.80, 0.30), (0, 0, 1)), focus=(-14, -24, 12), scale=60,
         labels=[("clips", "screw", 0, "L", "M3 × 20 button head screw  ×4", "2 per C-clip, through its foot\nand the plate"),
                 ("tcbase", "screw", 0, "L", "M3 × 25 button head screw  ×1", "tap-collar base, plain hole"),
                 ("tcbase", "screw", 1, "R", "M3 × 30 flat head screw  ×1",
                  "tap-collar base, countersunk hole. Only about\n3 mm comes through the plate in the CAD:\ncheck the locknut's nylon grips"),
                 ("clips", "nut", "low", "R", "M3 nylon-insert locknut  ×6", "under the plate: 4 for the C-clips,\n2 for the tap-collar base")]),
    dict(key="collar", n="5", title="Tap collar: clamp and solenoid (seen from behind)",
         parts=["Body1 <1>", "solenoid_coil <1>", "solenoid_plunger <1>", "solenoid_yoke <1>"],
         groups=["clamp", "solenoid"], only=None,
         view=((0.42, -0.80, 0.42), (0, 0, 1)), focus=(-18, -2, 54), scale=54,
         labels=[("clamp", "screw", 0, "R", "M3 × 20 button head screw  ×1", "clamp, across the collar's split"),
                 ("clamp", "nut", 0, "R", "M3 nylon-insert locknut  ×1", "on the clamp's far ear"),
                 ("solenoid", "screw", 0, "L", "M3 × 5 socket head cap screw  ×2",
                  "from behind the collar's flange\ninto the solenoid's frame")]),
    dict(key="stand", n="6", title="Stand: brackets to the Base, legs to the brackets",
         parts=["Part 1 <4>", "Part 1 <1>", "Part 1 <2>", "Part 1 <3>", "Part 1 <5>", "Part 1 <6>", "Part 1 <7>"],
         groups=["stand_base", "legs"], only=None,
         view=((0.70, -0.52, 0.50), (0, 0, 1)), focus=(-22, -70, -34), scale=196,
         labels=[("stand_base", "screw", 1, "R", "Stand bolt + nut  ×6, brackets to the Base",
                  "2 per bracket: side brackets on top of the Base,\nthe back bracket's rails under it"),
                 ("legs", "screw", 4, "L", "Stand bolt + nut  ×6, legs to the brackets",
                  "2 per leg, head outside the bracket"),
                 ("legs", "nut", 0, "R", "Stand nut", "on the inside of each leg")]),
]

COLOURS = None


def part_colours():
    from assembly_193 import GROUPS
    return {n: g[4] for g in GROUPS for n in g[3]}


def render_panel(P, J, spec, size):
    import pyvista as pv
    import vtk
    cols = part_colours()
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background("white")
    for n in spec["parts"]:
        ghost = n in spec.get("ghost", [])
        p.add_mesh(pv.wrap(P[n]), color=wash(cols[n]), smooth_shading=False, specular=0.1, ambient=0.25, diffuse=0.8,
                   opacity=0.32 if ghost else 1.0)
    sel = [j for j in J if j["group"] in spec["groups"] and (spec["only"] is None or spec["only"](j))]
    anchors = {}
    for j in sel:
        meshes, anc, (a, b) = fastener_scene(j)
        for m, c in meshes:
            p.add_mesh(pv.wrap(m), color=c, smooth_shading=True, specular=0.5, specular_power=20, ambient=0.2, diffuse=0.8)
        dl = dashes(a, b)
        if dl is not None:
            p.add_mesh(dl, color="#c0392b", line_width=4)
        anchors.setdefault(j["group"], []).append(anc)
    (vd, up), f, sc = spec["view"], np.array(spec["focus"], float), spec["scale"]
    p.enable_parallel_projection()
    p.camera_position = [tuple(f + 600 * unit(vd)), tuple(f), up]
    p.camera.parallel_scale = sc
    p.enable_anti_aliasing("ssaa")
    p.render()
    img = p.screenshot(return_img=True)
    coord = vtk.vtkCoordinate()
    coord.SetCoordinateSystemToWorld()
    H = img.shape[0]
    scr = {}
    for g, lst in anchors.items():
        scr[g] = []
        for anc in lst:
            d = {}
            for kk, pt in anc.items():
                coord.SetValue(*pt)
                x, y = coord.GetComputedDoubleDisplayValue(p.renderer)
                d[kk] = (x, H - y)
            scr[g].append(d)
    p.close()
    return img, scr


KEY = [("M3x14 SHCS", "M3 × 14\nsocket head", 8), ("M3x10 SHCS", "M3 × 10\nsocket head", 2),
       ("M3x5 SHCS", "M3 × 5\nsocket head", 2), ("M2.5x8 SHCS", "M2.5 × 8\nsocket head", 4),
       ("M3x20 BHCS", "M3 × 20\nbutton head", 5), ("M3x25 BHCS", "M3 × 25\nbutton head", 1),
       ("M3x30 FHCS", "M3 × 30\nflat head", 1), ("M5x40 BHCS", "M5 × 40\nbutton head", 2),
       ("M3 locknut", "M3 nylon-\ninsert\nlocknut", 15), ("M5 locknut", "M5 nylon-\ninsert\nlocknut", 2),
       ("stand bolt", "stand bolt\n¼-20 or M6,\nabout 25 mm", 12), ("stand nut", "stand\nnut", 12)]


def render_key(size, gap=11.5):
    """All the hardware for one doser, side by side at one scale, heads on one line."""
    import pyvista as pv
    import vtk
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background("white")
    x, pos = 0.0, []
    for kind, label, n in KEY:
        if kind in SCREWS:
            meshes, top = screw_meshes(kind)
            w = SCREWS[kind][3] * (1.155 if SCREWS[kind][0] == "hex" else 1.0)
            meshes = place(meshes, [x + w / 2, 0, -top], [0, 0, 1])
        else:
            w = NUTS[kind][0] * 1.155
            meshes = place(nut_meshes(kind), [x + w / 2, 0, -NUTS[kind][1]], [0, 0, 1])
        for m, c in meshes:
            p.add_mesh(pv.wrap(m), color=c, smooth_shading=True, specular=0.5, specular_power=20, ambient=0.2, diffuse=0.8)
        pos.append((x + w / 2, label, n))
        x += w + gap
    width = x - gap
    f = np.array([width / 2, 0, -21.5])
    p.enable_parallel_projection()
    p.camera_position = [tuple(f + 600 * unit([0, -1, 0.30])), tuple(f), (0, 0, 1)]
    p.camera.parallel_scale = max(size[1] / size[0] * width / 2 * 1.04, 24.5)
    p.enable_anti_aliasing("ssaa")
    p.render()
    img = p.screenshot(return_img=True)
    coord = vtk.vtkCoordinate()
    coord.SetCoordinateSystemToWorld()
    lab = []
    for px, label, n in pos:
        coord.SetValue(px, 0, 0)
        sx, _ = coord.GetComputedDoubleDisplayValue(p.renderer)
        lab.append((sx, label, n))
    p.close()
    return img, lab


def render_locator(P, J, size):
    """The assembled doser with every fastener in place, and where each panel is."""
    import pyvista as pv
    import vtk
    cols = part_colours()
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background("white")
    for n, m in P.items():
        p.add_mesh(pv.wrap(m), color=wash(cols[n], 0.5), smooth_shading=False, specular=0.1, ambient=0.25, diffuse=0.8)
    for j in J:
        for m, c in fastener_scene(j, explode=False)[0]:
            p.add_mesh(pv.wrap(m), color=c, smooth_shading=True, specular=0.5, ambient=0.2, diffuse=0.8)
    f = np.array([-18.0, -45.0, -40.0])
    p.enable_parallel_projection()
    p.camera_position = [tuple(f + 900 * unit([0.62, 0.66, 0.42])), tuple(f), (0, 0, 1)]
    p.camera.parallel_scale = 175
    p.enable_anti_aliasing("ssaa")
    p.render()
    img = p.screenshot(return_img=True)
    coord = vtk.vtkCoordinate()
    coord.SetCoordinateSystemToWorld()
    H = img.shape[0]
    marks = {}
    for k, pt in LOCATE.items():
        coord.SetValue(*pt)
        x, y = coord.GetComputedDoubleDisplayValue(p.renderer)
        marks[k] = (x, H - y)
    p.close()
    return img, marks


# where each panel's joints are, for the locator (panel number -> 3D point)
LOCATE = {"1": (56, 93, 10), "2": (38, 59.2, 37.4), "3": (16, -24, 52), "4": (-40, 16, 18), "5": (-30, 0, 72),
          "6": (115, 85, -7)}


def layout(ys, lo, hi, gap):
    order = np.argsort(ys)
    pos = np.array(ys, float)[order]
    pos = np.clip(pos, lo, hi)
    for k in range(1, len(pos)):
        pos[k] = max(pos[k], pos[k - 1] + gap)
    over = pos[-1] - hi if len(pos) else 0
    if over > 0:
        pos -= over
        for k in range(len(pos) - 2, -1, -1):
            pos[k] = min(pos[k], pos[k + 1] - gap)
    out = np.empty_like(pos)
    out[order] = pos
    return out


def render() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from assembly_193 import parts
    P = {name: m for g, name, m in parts(False)}
    J = joints()
    OUT.mkdir(exist_ok=True)

    PW, PH = 1000, 900               # one panel
    FW = 3 * PW + 40
    top, key_h = 150, 640
    FH = top + key_h + 2 * PH + 30
    fig = plt.figure(figsize=(FW / 100, FH / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FW); ax.set_ylim(FH, 0); ax.axis("off")
    ax.text(FW / 2, 22, "Powder doser (#193): where the hardware goes", ha="center", va="top", fontsize=34, fontweight="bold")
    ax.text(FW / 2, 82, "Every screw, nut and bolt for one doser, drawn pulled out along its hole; the red dashes run through the hole. "
            "Sizes from inventory-checklist.csv, hole positions from the Onshape assembly (f866631c, 7 Nov 2026).",
            ha="center", va="top", fontsize=16, color="#444444")

    # hardware key (left) and locator (right)
    KW = 1880
    kimg, klab = render_key((KW, 400))
    kx0, ky0 = 30, top + 50
    ax.text(kx0 + 10, top + 4, "Hardware for one doser (all drawn to the same scale)", fontsize=21, fontweight="bold", va="top")
    ax.imshow(kimg, extent=[kx0, kx0 + kimg.shape[1], ky0 + kimg.shape[0], ky0])
    for sx, label, n in klab:
        ax.text(kx0 + sx, ky0 + kimg.shape[0] + 6, f"×{n}", ha="center", va="top", fontsize=20, fontweight="bold", color="#1b1b1b")
        ax.text(kx0 + sx, ky0 + kimg.shape[0] + 40, label, ha="center", va="top", fontsize=12.5, color="#333333", linespacing=1.12)
    limg, marks = render_locator(P, J, (FW - KW - 90, key_h + 10))
    lx0, ly0 = KW + 70, top - 10
    ax.imshow(limg, extent=[lx0, lx0 + limg.shape[1], ly0 + limg.shape[0], ly0])
    ax.text(lx0 + 10, top + 4, "Where each panel is", fontsize=21, fontweight="bold", va="top")
    for k, (mx, my) in marks.items():
        ax.text(lx0 + mx, ly0 + my, k, fontsize=17, fontweight="bold", va="center", ha="center", color="white",
                bbox=dict(boxstyle="circle,pad=0.25", fc="#c0392b", ec="white", lw=1.5))

    for i, spec in enumerate(PANELS):
        r, c = divmod(i, 3)
        x0, y0 = 20 + c * PW, top + key_h + r * PH
        img, scr = render_panel(P, J, spec, (PW, PH - 70))
        iy0 = y0 + 70
        ax.imshow(img, extent=[x0, x0 + PW, iy0 + img.shape[0], iy0])
        ax.add_patch(plt.Rectangle((x0 + 6, y0 + 6), PW - 12, PH - 12, fill=False, ec="#c4ccd4", lw=1.2))
        ax.text(x0 + 24, y0 + 22, spec["n"], fontsize=22, fontweight="bold", va="top", ha="left", color="white",
                bbox=dict(boxstyle="circle,pad=0.25", fc="#2c3e50", ec="none"))
        ax.text(x0 + 70, y0 + 26, spec["title"], fontsize=17, fontweight="bold", va="top", ha="left")
        sides = {"L": [], "R": []}
        for lab in spec["labels"]:
            g, which, idx, side, bold, sub = lab
            pts = [np.array(a[which]) for a in scr[g] if which in a]
            if idx == "low":
                pt = max(pts, key=lambda q: q[1])
            else:
                pt = pts[min(idx, len(pts) - 1)]
            nudge = {"-": 150, "+": -40}.get(side[1:], 0)
            sides[side[0]].append((pt, bold, sub, nudge))
        for side, lst in sides.items():
            if not lst:
                continue
            ys = layout([iy0 + q[0][1] + q[3] for q in lst], iy0 + 30, y0 + PH - 90, 120)
            for (pt, bold, sub, _), y in zip(lst, ys):
                xt = x0 + 26 if side == "L" else x0 + PW - 26
                ha = "left" if side == "L" else "right"
                tb = ax.text(xt, y - 6, bold, ha=ha, va="bottom", fontsize=15, fontweight="bold", color="#1b1b1b",
                             bbox=dict(fc="white", ec="none", alpha=0.8, pad=1))
                ax.text(xt, y, sub, ha=ha, va="top", fontsize=12.5, color="#3d3d3d", linespacing=1.15,
                        bbox=dict(fc="white", ec="none", alpha=0.8, pad=1))
                bb = tb.get_window_extent(renderer=fig.canvas.get_renderer())
                tx = (bb.x1 + 8) if side == "L" else (bb.x0 - 8)
                ty = FH - (bb.y0 + bb.y1) / 2
                ax.plot([tx, x0 + pt[0]], [ty, iy0 + pt[1]], color="#2b2b2b", lw=1.1)
                ax.plot([x0 + pt[0]], [iy0 + pt[1]], marker="o", ms=6, color="#b03a2e", mec="white", mew=1)
    fig.savefig(OUT / "doser_193_hardware.png", dpi=100, facecolor="white")
    print("wrote", OUT / "doser_193_hardware.png")


if __name__ == "__main__":
    {"render": render}[sys.argv[1]]()
