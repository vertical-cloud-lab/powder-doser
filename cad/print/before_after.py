"""Before/after close-ups of the parts changed for printability, in print orientation.

    python before_after.py

Downward faces that need support (more than 50 deg from vertical, not on the bed) are drawn in orange.
The "before" meshes are the STLs exported from the parts as committed before the change (kept next to the
images, in <design>/changes/); "after" is the current <design>/stl/<part>.stl.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

HERE = Path(__file__).resolve().parent
import sys  # noqa: E402

sys.path.insert(0, str(HERE))
import audit as A  # noqa: E402
from slice import ORIENT  # noqa: E402

# design, part, crop box in the part's own frame (lo, hi), view (elev, azim), before / after notes
CHANGES = [
    ("paternoster", "gondola", ((226, -34, -50), (244, 34, -10)), (14, -25),
     "before: the saddle's V sides start 8 mm above the bar\n(Bambu Studio, supports off: \"floating regions\")",
     "after: the seat's cheeks stand on the bar;\nsame 0.6 mm clearance round the auger tube"),
    ("chain-carousel-v2", "carriage", ((-13, -12, 2), (13, 2, 17)), (8, 195),
     "before: the tab hook's finger is a 9.2 mm cantilever over the slot\n(Bambu Studio, supports off: \"floating cantilever\")",
     "after (print file only): a 0.8 mm break-off web across the slot's\nmouth makes the finger a bridge; cut it off flush after printing"),
]
OVER = "#eb6834"
BODY = np.array([0.62, 0.66, 0.72])


def crop(m: trimesh.Trimesh, lo, hi) -> trimesh.Trimesh:
    """The part of the mesh inside the box, capped (six plane cuts)."""
    for ax in range(3):
        n = np.zeros(3)
        n[ax] = 1.0
        o = np.zeros(3)
        o[ax] = lo[ax]
        m = m.slice_plane(o, n, cap=True)
        o[ax] = hi[ax]
        m = m.slice_plane(o, -n, cap=True)
    return m


def panel(ax, m: trimesh.Trimesh, zbed: float, view, title: str, cut_planes) -> None:
    n = m.face_normals
    c = m.triangles_center
    cut = np.zeros(len(m.faces), bool)               # faces of the crop box's caps are not overhangs
    for o, d in cut_planes:
        cut |= (np.abs((c - o) @ d) < 1e-3) & (np.abs(n @ d) > 0.999)
    down = (n[:, 2] < -np.sin(np.radians(A.OVERHANG_DEG))) & (m.triangles[:, :, 2].max(axis=1) > zbed + 0.02) & ~cut

    light = np.array([0.4, -0.5, 0.75])
    light /= np.linalg.norm(light)
    shade = 0.45 + 0.55 * np.clip(n @ light, 0, 1)
    cols = np.where(down[:, None], np.array(matplotlib.colors.to_rgb(OVER))[None, :] * (0.7 + 0.3 * shade[:, None]),
                    BODY[None, :] * shade[:, None])
    ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=np.clip(cols, 0, 1), edgecolors="none"))
    lo, hi = m.bounds
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(hi - lo)
    ax.view_init(*view)
    ax.set_axis_off()
    ax.set_title(title, fontsize=8.5, loc="left", color="#1f1f1c")


def main() -> None:
    for design, part, (lo, hi), view, t0, t1 in CHANGES:
        out = HERE / design / "changes"
        meshes = [trimesh.load(out / f"{part}_before.stl"), trimesh.load(HERE / design / "stl" / f"{part}.stl")]
        fig = plt.figure(figsize=(10, 4.6), dpi=140)
        for i, (m, t) in enumerate(zip(meshes, (t0, t1))):
            spec = ORIENT[part][0]
            full = m.copy()
            full.apply_transform(A.rot(spec))
            zbed = full.bounds[0][2]
            c = crop(m, lo, hi)
            c.apply_transform(A.rot(spec))
            R = A.rot(spec)[:3, :3]
            planes = []
            for ax_i in range(3):
                d = R @ np.eye(3)[ax_i]
                for v in (lo, hi):
                    o = np.zeros(3)
                    o[ax_i] = v[ax_i]
                    planes.append((R @ o, d))
            ax = fig.add_subplot(1, 2, i + 1, projection="3d")
            panel(ax, c, zbed, view, t, planes)
        fig.suptitle(f"{design} / {part}, print orientation (orange: faces > 50 deg from vertical that would need support)",
                     fontsize=9, x=0.01, ha="left", color="#33332f")
        fig.tight_layout()
        fig.savefig(out / f"{part}_before_after.png", facecolor="white")
        plt.close(fig)
        print(out / f"{part}_before_after.png")


if __name__ == "__main__":
    main()
