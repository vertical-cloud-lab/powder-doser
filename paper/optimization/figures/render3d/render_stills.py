#!/usr/bin/env python3
"""3D stills for the overview figure (``make_overview_relations.py``).

Every card in the figure gets a still rendered with the same PyVista/VTK toolkit
as the animated powder-test walkthroughs of PR #190 (``docs/powder-tests/render/``):

* **Standard tests (bottom row): stills from the #190 animations.** Each scene's own
  ``frame(t)`` poses its apparatus at a chosen moment of the procedure (powder running
  out of the Hall funnel, the cylinder on the tap tester, ...). The captions, chart and
  bench are left out, the camera is re-aimed to fit the whole apparatus, and the frame
  is rendered on the card's background colour.
* **Doser measurements (top row): new scenes.** #190 has no doser, so these are built
  here with #190's helpers (``render/common.py``) around the doser's CAD from PR #170
  (``cad/full-assembly``: the lab's Fusion STEP parts, placed by ``onshape/layout.py``
  at any tilt). Feed factor: the doser on its board at three tilts over a cup on a
  balance. "Ghost dose": a clear vessel without a screw, outlet closed, in the doser's
  own tap collar and solenoid. Angle of repose: the doser pours a pile that a camera
  watches from the side.

The doser's tilt, the pile and the fill levels are illustrative, like the numbers in
the #190 animations; nothing here is a measurement.

Neither #190 nor #170 is merged yet, so their files are read from wherever they are
checked out (by default, their in-tree locations once merged). The committed stills were
rendered from #190 at 1e0d6f8 and #170 at 7f5b3b7::

    git fetch origin claude/powder-test-animations-20261028 claude/issue-165-20261001-1931
    mkdir -p /tmp/pt /tmp/r170
    git archive 1e0d6f8 docs/powder-tests/render | tar -x -C /tmp/pt     # PR #190
    git archive 7f5b3b7 cad/full-assembly | tar -x -C /tmp/r170          # PR #170
    export POWDER_TESTS=/tmp/pt/docs/powder-tests/render DOSER_CAD=/tmp/r170/cad/full-assembly

Then, from ``paper/optimization/`` (needs pyvista, vtk, cadquery, numpy, pillow and an
X display; ``xvfb-run`` provides one)::

    xvfb-run -a python3 figures/render3d/render_stills.py          # all eight stills
    xvfb-run -a python3 figures/render3d/render_stills.py ff aor   # some of them

Writes ``figures/stills/<key>.png`` (cropped to the apparatus) and
``figures/stills/anchors.json`` (where labelled features land in each image, as
fractions of its width and height, for the figure's labels).
"""
from __future__ import annotations

import importlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE.parent / "stills"
POWDER_TESTS = Path(os.environ.get("POWDER_TESTS", REPO / "docs" / "powder-tests" / "render"))
DOSER_CAD = Path(os.environ.get("DOSER_CAD", REPO / "cad" / "full-assembly"))
CACHE = Path(os.environ.get("DOSER_MESH_CACHE", "/tmp/doser-mesh-cache"))

RW, RH = 2000, 1500                    # render size before cropping
TOP_BG, BOT_BG = "#eef4fd", "#fdf1ea"  # card fills in make_overview_relations.py
SAND, SAND_D = "#d9c49a", "#9c8456"    # powder colour used in the figure

# Bottom row: (#190 scene module, time in its animation, camera azimuth/elevation, zoom).
SCENES = {
    "hall": dict(module="hall_flow", t=11.0, az=-14, el=15, zoom=1.0),     # 316L running out
    "psd": dict(module="laser_diffraction", t=15.5, az=-26, el=24, zoom=1.0),  # rings lit
    "shear": dict(module="ring_shear", t=15.0, az=-18, el=24, zoom=1.0),   # shearing
    "tap": dict(module="density", t=21.0, az=-16, el=14, zoom=1.0),        # being tapped
    "moist": dict(module="moisture_lod", t=13.0, az=-18, el=24, zoom=1.0),  # drying
}
DOSER_KEYS = ("ff", "gd", "aor")
ALL_KEYS = DOSER_KEYS + tuple(SCENES)


# --------------------------------------------------------------------------- shared
def _common():
    sys.path.insert(0, str(POWDER_TESTS))
    import common  # noqa: E402  (#190's helpers)
    return common


def visible_bounds(st, skip=("bench",), skip_prefix=("sh_",)):
    b = np.array([np.inf, -np.inf] * 3)
    for name, a in st.pl.actors.items():
        if name in skip or name.startswith(skip_prefix) or not a.GetVisibility():
            continue
        bb = np.asarray(a.GetBounds(), float)
        if not np.all(np.isfinite(bb)) or bb[0] > bb[1]:
            continue
        b[0::2] = np.minimum(b[0::2], bb[0::2])
        b[1::2] = np.maximum(b[1::2], bb[1::2])
    return b


def aim(st, bounds, az, el, zoom=1.0, view_angle=30.0):
    """Look at the box `bounds` from azimuth/elevation (the #190 convention), fitted."""
    c = 0.5 * (bounds[0::2] + bounds[1::2])
    st.orbit(c, 1000.0, az, el, view_angle=view_angle)
    st.pl.camera.SetWindowCenter(0.0, 0.0)
    st.pl.reset_camera(bounds=list(bounds))
    st.pl.camera.zoom(zoom)
    st.pl.camera.clipping_range = (5, 8000)


def finish(st, key, bg, anchors_world=None):
    """Render at RW x RH on `bg`, crop to the apparatus, save, and return label anchors."""
    from PIL import Image
    st.pl.set_background(bg)
    st.pl.window_size = [RW, RH]
    st.w, st.h = RW, RH
    rgb = st.render()
    ref = np.array([int(bg[i:i + 2], 16) for i in (1, 3, 5)])
    mask = np.abs(rgb.astype(int) - ref).max(axis=2) > 5
    ys, xs = np.nonzero(mask)
    pad = int(0.025 * RW)
    x0, x1 = max(0, xs.min() - pad), min(RW, xs.max() + pad + 1)
    y0, y1 = max(0, ys.min() - pad), min(RH, ys.max() + pad + 1)
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb[y0:y1, x0:x1]).save(OUT / f"{key}.png", optimize=True)
    anchors = {}
    for name, xyz in (anchors_world or {}).items():
        px, py = st.project(xyz)
        anchors[name] = [round((px - x0) / (x1 - x0), 4), round((py - y0) / (y1 - y0), 4)]
    print(key, "->", OUT / f"{key}.png", f"{x1 - x0}x{y1 - y0}", flush=True)
    return {"size": [int(x1 - x0), int(y1 - y0)], "anchors": anchors}


# --------------------------------------------------------------------------- #190 stills
def still_from_scene(key):
    cfg = SCENES[key]
    _common()
    mod = importlib.import_module(cfg["module"])
    mod.compose = lambda rgb, ov, stage=None: None   # no title card, captions, chart
    mod.frame(cfg["t"])                               # poses everything at time t
    st = mod.st
    st.pose("bench", visible=False)
    aim(st, visible_bounds(st), cfg["az"], cfg["el"], cfg["zoom"])
    return finish(st, key, BOT_BG)


# --------------------------------------------------------------------------- doser CAD
PLA_BLUE = "#2f7fe0"   # the printed parts on the rig (11 Sep photo in #170)
PART_STYLE = {
    "Baseplate": ("pla", PLA_BLUE), "Mounting plate": ("pla", PLA_BLUE),
    "Bracket (rear)": ("pla", PLA_BLUE), "Bracket (front)": ("pla", PLA_BLUE),
    "Tap collar base (AI)": ("pla", PLA_BLUE), "Tap collar": ("pla", PLA_BLUE),
    "Stepper pinion": ("pla", PLA_BLUE), "Servo pinion (+X)": ("pla", PLA_BLUE),
    "Servo pinion (-X)": ("pla", PLA_BLUE),
    "Auger": ("pla", "#f4f3ef"), "Auger cap": ("pla", "#2342a0"),
    "Stepper (NEMA 11)": ("dark", "#2b2d31"), "Servo MG996R (+X)": ("dark", "#1f2023"),
    "Servo MG996R (-X)": ("dark", "#1f2023"), "Solenoid (Adafruit 412)": ("steel", None),
}


def _layout():
    sys.path.insert(0, str(DOSER_CAD / "onshape"))
    import layout  # noqa: E402  (#170's part placements)
    return layout


def part_mesh(rel):
    """A STEP part tessellated in its own frame (cached as .vtp)."""
    import pyvista as pv
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (rel.replace("/", "__") + ".vtp")
    if not f.exists():
        import cadquery as cq
        shp = cq.importers.importStep(str(DOSER_CAD / "components" / rel))
        verts, tris = cq.Compound.makeCompound(shp.vals()).tessellate(0.05, 0.25)
        v = np.array([(p.x, p.y, p.z) for p in verts])
        faces = np.hstack([np.full((len(tris), 1), 3), np.asarray(tris)]).ravel()
        pv.PolyData(v, faces).save(f)
    m = pv.read(f)
    return m.compute_normals(split_vertices=True, feature_angle=35, auto_orient_normals=False)


def add_doser(st, tilt, M0, prefix="d", only=None, opacity=None):
    """Add the doser's parts at `tilt` (deg, outlet down), placed by M0 @ layout.

    Returns the layout's placements (name -> world 4x4 including M0)."""
    common = _common()
    layout = _layout()
    pl = {}
    for name, (rel, M) in layout.placements(tilt).items():
        if only is not None and name not in only:
            continue
        kind, col = PART_STYLE[name]
        style = dict(common.MAT["steel"]) if kind == "steel" else dict(
            color=col, specular=0.25 if kind == "pla" else 0.35, specular_power=18,
            diffuse=0.85, ambient=0.2)
        if opacity is not None:
            style["opacity"] = opacity
        st.add(f"{prefix}:{name}", part_mesh(rel).transform(M0 @ M, inplace=False), style)
        pl[name] = M0 @ M
    return pl


def pt(M, p):
    return (M @ np.array([*p, 1.0]))[:3]


def board_on_legs(st, z0, common):
    """The board the doser is screwed to (#170: its legs hang over the front edge),
    standing on four legs so the balance or the pile fits under the outlet."""
    layout = _layout()
    yf, bt = layout.BOARD_FRONT_Y, layout.BOARD_T
    st.add("board", common.box(-125, 125, yf, yf + 160, z0 - bt, z0), "white")
    for k, (x, y) in enumerate((sx * 112, yy) for sx in (1, -1) for yy in (yf + 13, yf + 147)):
        st.add(f"leg{k}", common.rod((x, y, 0), (x, y, z0 - bt), 7), "steel_dark")
        st.shadow(f"sh_leg{k}", (x, y), 16, 16, 0.30)


def balance(st, xy, common, z_pan=62.0):
    x, y = xy
    st.add("bal_body", common.box(x - 78, x + 78, y - 95, y + 85, 0, 46), "light")
    st.add("bal_lcd", common.box(x - 50, x + 50, y - 96.5, y - 95, 12, 34), "lcd")
    st.add("bal_post", common.rod((x, y, 46), (x, y, z_pan - 3), 6), "steel_dark")
    st.add("bal_pan", common.disc(44, z_pan - 3, z_pan).translate((x, y, 0), inplace=False), "steel")
    st.shadow("sh_bal", (x, y - 5), 110, 120, 0.32)
    return z_pan


def falling_grains(p0, p1, n, seed, spread=1.6):
    """Grains strung out along a short ballistic drop from p0 to p1 (a still of a stream)."""
    rng = np.random.default_rng(seed)
    s = np.sort(rng.random(n)) ** 1.4
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    pts = p0[None, :] + (p1 - p0)[None, :] * s[:, None]
    pts[:, :2] += rng.normal(0, 1, (n, 2)) * (0.4 + spread * s[:, None])
    return pts


# --------------------------------------------------------------------------- doser scenes
def scene_feed_factor():
    """The doser at 0, 20 and 40 degrees over a cup on a balance (20 degrees drawn solid)."""
    common = _common()
    st = common.Stage(bench=None, w=RW, h=RH)
    z0 = 160.0
    M0 = common.matrix(translate=(0, 0, z0))
    tilt = 20.0
    pl = add_doser(st, tilt, M0)
    for k, tg in enumerate((0.0, 40.0)):   # the barrel at the other tilts, ghosted
        add_doser(st, tg, M0, prefix=f"g{k}", only=("Auger", "Auger cap"), opacity=0.22)
    board_on_legs(st, z0, common)
    out = pt(pl["Auger"], (0, 0, 0))
    z_pan = balance(st, (out[0], out[1]), common)
    # cup on the pan, a little powder in it, and the stream
    cup_r, cup_h = 20.0, 26.0
    cx, cy = out[0], out[1]
    st.add("cup", common.lathe([(0, z_pan), (cup_r - 2, z_pan), (cup_r, z_pan + cup_h), (cup_r - 1.4, z_pan + cup_h),
                                (cup_r - 3.2, z_pan + 1.6), (0, z_pan + 1.6)]).translate((cx, cy, 0), inplace=False),
           "glass", opacity=0.45)
    tan_t = math.tan(math.radians(33))
    st.add("cup_pow", common.heap_solid(cup_r - 3.4, 6.5, tan_t, z_pan + 1.6).translate((cx, cy, 0), inplace=False),
           "powder", color=SAND)
    g = falling_grains(out + np.array([0, 0, -2.0]), (cx, cy, z_pan + 1.6 + 6.0), 70, seed=3)
    st.grains("stream", g, common.grain_colors(len(g), SAND_D, 0.12, seed=4), size=7.0)
    # tilt arc around the hinge, beside the barrel's far end, with arrowheads
    layout = _layout()
    hinge = np.array([0.0, layout.HINGE_Y, layout.HINGE_Z + z0])
    R, xs = 230.0, 48.0
    ph = np.radians(np.linspace(-1, 41, 60))
    arc = np.c_[np.full_like(ph, xs), hinge[1] + R * np.cos(ph), hinge[2] + R * np.sin(ph)]
    st.add("arc", common.pv.Spline(arc, 120).tube(radius=1.6), "blue")
    for a, sgn in ((ph[0], -1), (ph[-1], 1)):
        tip = np.array([xs, hinge[1] + R * math.cos(a), hinge[2] + R * math.sin(a)])
        tang = sgn * np.array([0, -math.sin(a), math.cos(a)])
        st.add(f"arrow{sgn}", common.pv.Cone(center=tip + 5 * tang, direction=tang, height=12, radius=5.0,
                                             resolution=24), "blue")
    aim(st, visible_bounds(st, skip=("arc", "arrow-1", "arrow1")), az=66, el=14, zoom=1.0)
    return finish(st, "ff", TOP_BG)


def scene_ghost_dose():
    """A clear vessel (no screw), outlet closed, in the doser's tap collar and solenoid."""
    common = _common()
    layout = _layout()
    pv = common.pv
    st = common.Stage(bench=None, w=RW, h=RH)
    P = layout.placements(0.0)
    M_aug, M_col = P["Auger"][1], P["Tap collar"][1]
    # the auger axis in the collar's frame: where the collar's bore is, and its direction
    inv = np.linalg.inv(M_col)
    a0, a1 = pt(inv @ M_aug, (0, 0, 0)), pt(inv @ M_aug, (0, 0, 100))
    ax_dir = (a1 - a0) / np.linalg.norm(a1 - a0)
    # tube radius from the auger's mid-length (the printed barrel's outside)
    aug = part_mesh(P["Auger"][0])
    mid = aug.points[aug.points[:, 2] > 200]      # (vertices exist only at face ends)
    r_out = float(np.hypot(mid[:, 0], mid[:, 1]).max())
    r_in, L, z_b = r_out - 1.2, 150.0, 22.0       # thin SLA wall; vessel length; bottom
    # vessel frame: axis vertical, outlet (closed) at the bottom
    st.add("foot", common.disc(r_out + 13, 0, 6), dict(color=PLA_BLUE, specular=0.25, specular_power=18,
                                                       diffuse=0.85, ambient=0.2))
    st.shadow("sh_foot", (0, 0), r_out + 26, r_out + 26, 0.32)
    st.add("plug", common.lathe([(0, 6), (r_out + 2.5, 6), (r_out + 2.5, z_b + 4), (r_in - 0.2, z_b + 4),
                                 (r_in - 0.2, z_b), (0, z_b)]), "dark")
    st.add("vessel", common.lathe([(r_in, z_b), (r_out, z_b), (r_out, z_b + L), (r_in, z_b + L)], res=128),
           "glass", opacity=0.30)
    cap = part_mesh(P["Auger cap"][0])            # the doser's own fill cap on top
    st.add("cap", cap.transform(common.matrix(translate=(0, 0, z_b + L)), inplace=False),
           dict(color="#2342a0", specular=0.25, specular_power=18, diffuse=0.85, ambient=0.2))
    z_tap, z_bulk = z_b + 78.0, z_b + 96.0
    st.add("powder", common.lathe([(0, z_b), (r_in - 0.3, z_b), (r_in - 0.3, z_tap), (0, z_tap)], res=96),
           "powder", color=SAND)
    rng = np.random.default_rng(5)
    th = rng.uniform(0, 2 * np.pi, 900)
    zz = rng.uniform(z_b + 1, z_tap - 0.5, 900)
    g = np.c_[(r_in - 0.1) * np.cos(th), (r_in - 0.1) * np.sin(th), zz]
    st.grains("grains", g, common.grain_colors(len(g), SAND_D, 0.15, seed=6), size=5.0)
    # where the powder stood before tapping (bulk): a faint layer, and the two level rings
    st.add("bulk_ghost", common.lathe([(0, z_tap), (r_in - 0.3, z_tap), (r_in - 0.3, z_bulk), (0, z_bulk)]),
           "powder", color=SAND, opacity=0.22)
    blue = dict(color="#2a6fc9", specular=0.3, specular_power=20, diffuse=0.8, ambient=0.25)
    ring = pv.ParametricTorus(ringradius=r_out + 0.9, crosssectionradius=0.9)
    st.add("ring_tap", ring.translate((0, 0, z_tap), inplace=False), blue)
    for k in range(18):                           # dashed ring at the bulk level
        a = np.radians(np.linspace(k * 20, k * 20 + 11, 8))
        seg = np.c_[(r_out + 0.9) * np.cos(a), (r_out + 0.9) * np.sin(a), np.full_like(a, z_bulk)]
        st.add(f"ring_bulk{k}", pv.Spline(seg, 16).tube(radius=0.9), blue)
    # the doser's tap collar and solenoid, with the bore on the vessel axis
    # collar frame -> vessel frame: bore axis -> +z, solenoid side -> +x, at height z_c
    z_c = z_b + 30.0
    e_z = ax_dir
    sol = pt(np.linalg.inv(M_col) @ P["Solenoid (Adafruit 412)"][1], (0, 0, 0)) - a0
    e_x = sol - np.dot(sol, e_z) * e_z
    e_x /= np.linalg.norm(e_x)
    e_y = np.cross(e_z, e_x)
    Rm = np.vstack([e_x, e_y, e_z])               # rows: collar-frame axes -> vessel x, y, z
    s_c = float(np.dot(-a0, e_z))                 # the collar's own origin, along the axis
    Mc = np.eye(4)
    Mc[:3, :3] = Rm
    Mc[:3, 3] = -Rm @ (a0 + s_c * e_z) + np.array([0, 0, z_c])
    for name in ("Tap collar", "Solenoid (Adafruit 412)"):
        rel, M = P[name]
        Mloc = Mc @ np.linalg.inv(M_col) @ M
        kind, col = PART_STYLE[name]
        style = dict(common.MAT["steel"]) if kind == "steel" else dict(
            color=col, specular=0.25, specular_power=18, diffuse=0.85, ambient=0.2)
        st.add(f"c:{name}", part_mesh(rel).transform(Mloc, inplace=False), style)
    sol_c = pt(Mc @ np.linalg.inv(M_col) @ P["Solenoid (Adafruit 412)"][1], (0, -7.0, 31.05))
    aim(st, visible_bounds(st), az=24, el=16, zoom=1.0)
    return finish(st, "gd", TOP_BG, {
        "bulk": (-(r_out + 1.0) * 0.97, -(r_out + 1.0) * 0.26, z_bulk),
        "tapped": (-(r_out + 1.0) * 0.97, -(r_out + 1.0) * 0.26, z_tap),
        "tap": tuple(sol_c),
        "closed": (0.9 * (r_out + 2.5), -0.42 * (r_out + 2.5), (6 + z_b + 4) / 2),
    })


def scene_angle_of_repose():
    """The doser pours a pile on a round base; a camera watches it from the side."""
    common = _common()
    pv = common.pv
    st = common.Stage(bench=None, w=RW, h=RH)
    z0 = 160.0
    M0 = common.matrix(translate=(0, 0, z0))
    pl = add_doser(st, 24.0, M0)
    board_on_legs(st, z0, common)
    out = pt(pl["Auger"], (0, 0, 0))
    # base on a short pedestal, pile with grains, stream onto the apex
    R, z_b = 56.0, 52.0
    theta = 33.0
    tan_t = math.tan(math.radians(theta))
    apex = R * tan_t
    c = np.array([out[0], out[1], 0.0])
    st.add("ped", common.rod((c[0], c[1], 0), (c[0], c[1], z_b - 4), 9), "steel_dark")
    st.add("ped_foot", common.disc(34, 0, 4).translate((c[0], c[1], 0), inplace=False), "dark")
    st.add("base", common.disc(R, z_b - 4, z_b).translate((c[0], c[1], 0), inplace=False), "alu")
    st.shadow("sh_ped", (c[0], c[1]), 60, 60, 0.32)
    st.add("pile", common.heap_solid(R, apex, tan_t, z_b, n=36).translate((c[0], c[1], 0), inplace=False),
           "powder", color=SAND)
    zf = lambda r, th: z_b + np.maximum(0.05, apex - r * tan_t)  # noqa: E731
    at = common.surface_grains(1400, R - 0.5, zf, seed=8, lift=0.4)
    g = at() + np.array([c[0], c[1], 0])
    st.grains("pile_grains", g, common.grain_colors(len(g), SAND_D, 0.15, seed=9), size=5.0)
    gs = falling_grains(out + np.array([0, 0, -2.0]), (c[0], c[1], z_b + apex), 60, seed=10, spread=1.2)
    st.grains("stream", gs, common.grain_colors(len(gs), SAND_D, 0.12, seed=11), size=7.0)
    # the camera: body, lens and a post, level with the pile, aimed at it
    cam_p = np.array([c[0] - 170.0, c[1] - 60.0, z_b + apex * 0.5])
    d = c + np.array([0, 0, z_b + apex * 0.45]) - cam_p
    d /= np.linalg.norm(d)
    yaw = math.degrees(math.atan2(d[1], d[0]))
    body = common.box(-22, 14, -17, 17, -15, 15)
    lens = common.rod((14, 0, 0), (34, 0, 0), 10.5)
    glass = common.disc(8.5, 0, 1.2).rotate_y(90, inplace=False).translate((34.2, 0, 0), inplace=False)
    Mc = common.matrix(translate=cam_p) @ common.matrix(rot_deg=yaw)
    st.add("cam_body", body.transform(Mc, inplace=False), "dark")
    st.add("cam_lens", lens.transform(Mc, inplace=False), "mid")
    st.add("cam_glass", glass.transform(Mc, inplace=False), dict(color="#9fb8d6", specular=1.0,
                                                                  specular_power=80, diffuse=0.6, ambient=0.3))
    st.add("cam_post", common.rod((cam_p[0], cam_p[1], 0), (cam_p[0], cam_p[1], cam_p[2] - 15), 4), "steel_dark")
    st.add("cam_foot", common.disc(22, 0, 3).translate((cam_p[0], cam_p[1], 0), inplace=False), "dark")
    st.shadow("sh_cam", (cam_p[0], cam_p[1]), 34, 34, 0.30)
    # field of view: a faint cone from the lens to the pile
    tip = cam_p + d * 34
    fov = pv.Cone(center=tip + d * 75, direction=-d, height=150, radius=58, resolution=48, capping=False)
    st.add("fov", fov, dict(color="#7fa7d6", opacity=0.10, specular=0.0, diffuse=0.6, ambient=0.6))
    az = 28.0
    aim(st, visible_bounds(st, skip=("fov",)), az=az, el=10, zoom=1.0)
    # anchors for the angle label: the right foot of the pile's outline, a point along the
    # base towards the centre, and the apex (in the plane through the axis, across the view)
    e = np.array([math.cos(math.radians(az)), math.sin(math.radians(az)), 0.0])
    foot = c + np.array([0, 0, z_b]) + R * e
    return finish(st, "aor", TOP_BG, {
        "foot": tuple(foot), "along": tuple(foot - 0.5 * R * e),
        "apex": tuple(c + np.array([0, 0, z_b + apex])),
    })


DOSER_SCENES = {"ff": scene_feed_factor, "gd": scene_ghost_dose, "aor": scene_angle_of_repose}


# --------------------------------------------------------------------------- driver
def render_one(key):
    info = DOSER_SCENES[key]() if key in DOSER_SCENES else still_from_scene(key)
    (OUT / f".{key}.json").write_text(json.dumps(info))


def main(argv):
    if argv[:1] == ["--one"]:
        render_one(argv[1])
        return
    keys = argv or list(ALL_KEYS)
    for k in keys:
        if k not in ALL_KEYS:
            raise SystemExit(f"unknown still {k!r}; choose from {', '.join(ALL_KEYS)}")
    env = dict(os.environ, LP_NUM_THREADS=os.environ.get("LP_NUM_THREADS", "2"))
    for k in keys:   # one process per still: each #190 scene builds its own render window
        for attempt in range(3):
            if subprocess.run([sys.executable, __file__, "--one", k], env=env).returncode == 0:
                break
            print(f"retrying {k} ({attempt + 1})", file=sys.stderr)
        else:
            raise SystemExit(f"{k} failed")
    path = OUT / "anchors.json"
    allinfo = json.loads(path.read_text()) if path.exists() else {}
    for k in keys:
        f = OUT / f".{k}.json"
        allinfo[k] = json.loads(f.read_text())
        f.unlink()
    path.write_text(json.dumps(dict(sorted(allinfo.items())), indent=1) + "\n")
    print("wrote", path)


if __name__ == "__main__":
    main(sys.argv[1:])
