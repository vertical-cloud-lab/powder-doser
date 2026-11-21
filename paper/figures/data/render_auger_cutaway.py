#!/usr/bin/env python3
"""Shaded 3-D cut-away of the tested auger and its screw-on cap (Fig. 1c).

The auger and cap that ran every test are the team's Fusion 360 parts
("Threaded Auger Final" and "Cap Final", shared as STL in the issue #117
zip and committed under cad/full-assembly/components/fusion/ in PR #170).
This script screws the cap onto the tube, cuts both parts in half with the
plane through the tube axis (y = 0), keeps the far half (y >= 0), and closes
the cut with flat section faces so the inside reads as a cut-away: the plain
reservoir, the flight wrapped round the core near the outlet, the tapered
outlet and its 3 mm exit hole, the 44-tooth gear, the cap thread and the cap.

The cap is seated on the tube end (z = 250 mm) and turned 180 deg about the
axis, which puts its internal thread in the grooves of the tube's thread (as
exported, the two threads would occupy the same space).  The render is
orthographic and lit, drawn upright (outlet at the bottom), and seen from
slightly above, turned toward the viewer.  The cut faces are flat and darker
than the lit surfaces, and outlined, so they read as a section.  The image
is written to assets/auger_cutaway.png with a transparent background,
cropped tight.  The PNG's "anchors" text chunk holds JSON with the image
positions of the labelled features and the affine projection from the part
frame (mm) to image pixels; make_figures.py reads it to place the Fig. 1c
leader and dimension lines, so they follow the render if it changes.

Usage:
    python3 render_auger_cutaway.py                     # STLs from PR #170's branch
    python3 render_auger_cutaway.py AUGER.stl CAP.stl   # or from local files

Requires pyvista (VTK), trimesh, shapely, mapbox_earcut, numpy and Pillow.
Runs headless: without a display VTK falls back to EGL (or use xvfb-run).
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pyvista as pv
import trimesh
from PIL import Image, ImageFilter, PngImagePlugin
from shapely.geometry import Polygon

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_auger_section import CAP_SEAT_Z, _load  # noqa: E402

OUT = HERE.parent / "assets" / "auger_cutaway.png"

CAP_TURN_DEG = 180.0   # cap thread ridges then sit in the tube's grooves
AZ_DEG = 28.0          # camera turned from square-on to the cut face (+x)
EL_DEG = 34.0          # camera height above the horizontal
MODEL_PX = 2400        # rendered height of the part, in pixels
MARGIN = 0.02          # fraction of the height left around the part

BODY = {"auger": "#d6b26a", "cap": "#46649f"}   # lit outside and inside surfaces
CUT = {"auger": "#7d4c14", "cap": "#1f3260"}    # flat section faces
EDGE = (40, 40, 40)                             # section and outer outlines
LIGHTS = (  # direction from the part, intensity
    ((-0.9, -1.0, 0.9), 0.70),     # key: upper left, in front
    ((1.0, -0.4, 0.2), 0.30),      # fill: right
    ((0.0, 0.2, 1.0), 0.40),       # top: lights the upper faces of the flight
    (None, 0.22),                  # along the view
)

# labelled features (mm, in the part frame; the cut face is y = 0)
ANCHORS = {
    "cap": (14.0, 3.9, 239.0),          # outside of the cap
    "thread": (12.3, 0.0, 233.0),       # tube thread at the fill opening, cut
    "reservoir": (-5.0, 9.2, 165.0),    # bore wall behind the cut
    "gear": (22.3, 5.9, 83.3),          # tooth tips
    "flight": (7.25, 0.0, 52.3),        # a cut blade, right of the core
    "core": (0.0, 0.0, 62.0),           # core section
    "outlet": (5.2, 3.0, 6.0),          # cone of the tapered outlet
}


def _section(mesh: trimesh.Trimesh) -> list[Polygon]:
    """Solid region of the plane y = 0 through the axis, in (x, z)."""
    sec = mesh.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0])
    geom = None
    for loop in sec.discrete:
        if len(loop) < 4:
            continue
        poly = Polygon(np.c_[loop[:, 0], loop[:, 2]]).buffer(0)
        geom = poly if geom is None else geom.symmetric_difference(poly)
    parts = geom.geoms if hasattr(geom, "geoms") else [geom]
    return [p for p in parts if p.geom_type == "Polygon" and p.area > 0.01]


def _cut_face(polys: list[Polygon]) -> pv.PolyData:
    """Triangulated section faces in the plane y = 0, facing -y."""
    verts, faces, off = [], [], 0
    for p in polys:
        v2, f = trimesh.creation.triangulate_polygon(p, engine="earcut")
        verts.append(np.c_[v2[:, 0], np.zeros(len(v2)), v2[:, 1]])
        faces.append(f + off)
        off += len(v2)
    v, f = np.concatenate(verts), np.concatenate(faces)
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    flip = np.cross(b - a, c - a)[:, 1] > 0
    f[flip] = f[flip][:, ::-1]
    return pv.PolyData(v, np.c_[np.full(len(f), 3), f].ravel())


def _outline(polys: list[Polygon], y: float = -0.05) -> pv.PolyData:
    """Boundary lines of the section faces, nudged toward the camera."""
    pts, lines, off = [], [], 0
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            c = np.asarray(ring.coords)
            pts.append(np.c_[c[:, 0], np.full(len(c), y), c[:, 1]])
            lines.append(np.r_[len(c), np.arange(off, off + len(c))])
            off += len(c)
    return pv.PolyData(np.concatenate(pts), lines=np.concatenate(lines))


def _half(mesh: trimesh.Trimesh) -> pv.PolyData:
    """The half of the part behind the cut (y >= 0), as an open surface."""
    half = trimesh.intersections.slice_mesh_plane(
        mesh, plane_normal=[0, 1, 0], plane_origin=[0, 0, 0], cap=False)
    faces = np.c_[np.full(len(half.faces), 3), half.faces].ravel()
    return pv.PolyData(np.asarray(half.vertices), faces)


def _view() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Unit vectors: toward the camera, screen right, and screen up."""
    az, el = np.deg2rad(AZ_DEG), np.deg2rad(EL_DEG)
    d = np.array([np.sin(az) * np.cos(el), -np.cos(az) * np.cos(el),
                  np.sin(el)])
    right = np.cross([0.0, 0.0, 1.0], d)
    right /= np.linalg.norm(right)
    return d, right, np.cross(d, right)


def _outer_outline(img: np.ndarray, width: int = 3) -> np.ndarray:
    """Draw a dark line round the part's silhouette (image space)."""
    alpha = Image.fromarray(img[..., 3])
    inner = np.asarray(alpha.filter(ImageFilter.MinFilter(2 * width + 1)),
                       dtype=float) / 255.0
    a = img[..., 3].astype(float) / 255.0
    ring = np.clip(a - inner, 0.0, 1.0)[..., None]
    out = img.astype(float)
    out[..., :3] = out[..., :3] * (1 - ring) + np.asarray(EDGE) * ring
    return out.round().astype(np.uint8)


def main() -> None:
    args = sys.argv[1:] + [None, None]
    parts = {"auger": _load(args[0], "threaded-auger-final.stl"),
             "cap": _load(args[1], "cap-final.stl")}
    parts["cap"].apply_transform(trimesh.transformations.rotation_matrix(
        np.deg2rad(CAP_TURN_DEG), [0, 0, 1]))
    parts["cap"].apply_translation([0, 0, CAP_SEAT_Z])

    # fit the window to the part's projected outline
    d, right, up = _view()
    pts = np.concatenate([m.vertices for m in parts.values()])
    u, v = pts @ right, pts @ up
    span_v = (v.max() - v.min()) * (1 + 2 * MARGIN)
    span_u = (u.max() - u.min()) + (v.max() - v.min()) * 2 * MARGIN
    height = int(round(MODEL_PX * (1 + 2 * MARGIN)))
    width = int(round(height * span_u / span_v))
    centre = (0.5 * (u.max() + u.min()) * right
              + 0.5 * (v.max() + v.min()) * up)

    pl = pv.Plotter(off_screen=True, window_size=(width, height),
                    lighting="none")
    for name, mesh in parts.items():
        polys = _section(mesh)
        pl.add_mesh(_half(mesh), color=BODY[name], smooth_shading=True,
                    split_sharp_edges=True, feature_angle=35, ambient=0.2,
                    diffuse=0.8, specular=0.2, specular_power=15)
        pl.add_mesh(_cut_face(polys), color=CUT[name], lighting=False)
        pl.add_mesh(_outline(polys), color=np.asarray(EDGE) / 255,
                    line_width=2.5, lighting=False)
    for direction, intensity in LIGHTS:
        vec = d if direction is None else np.asarray(direction, float)
        pl.add_light(pv.Light(position=centre + 600 * vec / np.linalg.norm(vec),
                              focal_point=centre, intensity=intensity,
                              light_type="scene light"))
    pl.enable_parallel_projection()
    pl.camera.focal_point = centre
    pl.camera.position = centre + 1000 * d
    pl.camera.up = tuple(up)
    pl.camera.parallel_scale = 0.5 * span_v
    pl.camera.clipping_range = (1.0, 2000.0)
    pl.enable_anti_aliasing("ssaa")
    img = pl.screenshot(transparent_background=True, return_img=True)

    # world (mm) -> image pixel (column, row from the top): affine, because
    # the projection is orthographic; fitted to VTK's own transform
    ren = pl.renderer
    probe = np.array([[x, y, z] for x in (-30, 30) for y in (-30, 30)
                      for z in (0, 250)], float)
    disp = []
    for p in probe:
        ren.SetWorldPoint(*p, 1.0)
        ren.WorldToDisplay()
        col, row, _ = ren.GetDisplayPoint()
        disp.append([col, img.shape[0] - row])
    pl.close()
    coef, *_ = np.linalg.lstsq(np.c_[probe, np.ones(len(probe))],
                               np.asarray(disp), rcond=None)
    A, b = coef[:3].T, coef[3]

    # crop to the part (plus a small margin) and outline it
    img = _outer_outline(img)
    alpha = img[..., 3]
    rows = np.flatnonzero(alpha.max(axis=1) > 0)
    cols = np.flatnonzero(alpha.max(axis=0) > 0)
    m = 6
    r0, r1 = max(rows[0] - m, 0), min(rows[-1] + m + 1, img.shape[0])
    c0, c1 = max(cols[0] - m, 0), min(cols[-1] + m + 1, img.shape[1])
    img = np.ascontiguousarray(img[r0:r1, c0:c1])
    b = b - [c0, r0]
    meta = {
        "anchors": {k: np.round(A @ xyz + b, 1).tolist()
                    for k, xyz in ANCHORS.items()},
        "projection": {"A": np.round(A, 6).tolist(),
                       "b": np.round(b, 3).tolist(),
                       "note": "pixel = A @ (x, y, z) + b; mm, part frame "
                               "(outlet at z = 0, cut face y = 0)"},
        "view": {"azimuth_deg": AZ_DEG, "elevation_deg": EL_DEG,
                 "projection": "orthographic", "cap_turn_deg": CAP_TURN_DEG},
    }
    info = PngImagePlugin.PngInfo()
    info.add_text("anchors", json.dumps(meta))
    Image.fromarray(img).save(OUT, pnginfo=info, optimize=True)
    print(json.dumps(meta))
    print(f"wrote {OUT} ({img.shape[1]} x {img.shape[0]} px)")


if __name__ == "__main__":
    main()
