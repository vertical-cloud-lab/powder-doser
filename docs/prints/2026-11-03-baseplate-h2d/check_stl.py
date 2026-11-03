#!/usr/bin/env python3
"""Check an STL against Onshape's own orthographic renders of the Baseplate.

    python check_stl.py PART.stl VIEWS_DIR

VIEWS_DIR holds top.png, front.png and right.png from Onshape's shadedviews endpoint at
0.2 mm per pixel (alpha = part). The STL is projected the same way, and each pair of
silhouettes is compared after aligning their bounding boxes. Reads geometry only.
"""
import sys
import numpy as np
import trimesh
from PIL import Image, ImageDraw

PX = 0.2  # mm per pixel
stl, views = sys.argv[1], sys.argv[2]
m = trimesh.load_mesh(stl, force="mesh")
lo, hi = m.bounds
print(f"triangles {len(m.faces)}, watertight {m.is_watertight}, volume {m.volume / 1000:.2f} cm3")
print("extent mm:", np.round(hi - lo, 2).tolist())


def silhouette(axes, flip_y=True):
    """Project onto two model axes; rasterise every triangle at PX mm/px."""
    v = m.vertices[:, axes]
    v = (v - v.min(axis=0)) / PX
    w, h = (np.ceil(v.max(axis=0)) + 1).astype(int)
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    for tri in m.faces:
        p = v[tri]
        pts = [(x, (h - 1 - y) if flip_y else y) for x, y in p]
        d.polygon(pts, fill=255)
    return np.asarray(img) > 0


def onshape_mask(name):
    a = np.asarray(Image.open(f"{views}/{name}.png").convert("RGBA"))[..., 3] > 0
    ys, xs = np.nonzero(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def compare(name, mine):
    ref = onshape_mask(name)
    h, w = max(ref.shape[0], mine.shape[0]), max(ref.shape[1], mine.shape[1])
    A = np.zeros((h, w), bool); B = np.zeros((h, w), bool)
    A[:ref.shape[0], :ref.shape[1]] = ref; B[:mine.shape[0], :mine.shape[1]] = mine
    best = None
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            Bs = np.roll(np.roll(B, dy, 0), dx, 1)
            iou = (A & Bs).sum() / max(1, (A | Bs).sum())
            if best is None or iou > best[0]:
                best = (iou, dx, dy, (A ^ Bs).sum())
    print(f"{name}: onshape {ref.shape[1] * PX:.1f} x {ref.shape[0] * PX:.1f} mm, stl {mine.shape[1] * PX:.1f} x {mine.shape[0] * PX:.1f} mm,"
          f" IoU {best[0]:.4f}, mismatched px {best[3]} (shift {best[1]},{best[2]})")
    return best[0]


# Onshape's named views: top looks down -Z (x right, y up); front looks along +Y (x right, z up);
# right looks along -X (y right, z up).
ious = [compare("top", silhouette([0, 1])), compare("front", silhouette([0, 2])), compare("right", silhouette([1, 2]))]
print("all silhouettes IoU >= 0.98:", all(i >= 0.98 for i in ious))
