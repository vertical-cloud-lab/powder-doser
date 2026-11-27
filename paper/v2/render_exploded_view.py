#!/usr/bin/env python3
"""Fig. 1b and SI Fig. S4 (v2): render PR #170's exploded view without balloons.

Review of 17 Nov 2026, point 1.2 (paper/review_2026-11-17/NOTES.md): the
exploded view in Fig. 1b had all 25 bill-of-materials balloons baked in by
PR #170's ``assembly_bom.py``, with leaders crossing the whole image.  This
script re-renders the same exploded start, from the same camera, without any
balloons, and writes a part-ID map so that make_exploded_view.py can put each
balloon right beside its own part.

It needs the PR #170 pipeline (branch ``claude/issue-165-20261001-1931``,
commit 7f5b3b7, ``cad/full-assembly/``), which needs cadquery and vtk.  Those
have no wheels for Python 3.14, so it was run in a Python 3.12 venv:

    git archive 7f5b3b7 cad/full-assembly | tar -x -C /tmp/fa
    uv venv -p 3.12 /tmp/fa_venv && VIRTUAL_ENV=/tmp/fa_venv uv pip install cadquery vtk trimesh pillow numpy
    xvfb-run -a /tmp/fa_venv/bin/python render_exploded_view.py /tmp/fa/cad/full-assembly

Writes, in assets/exploded/:

    exploded_render.png   the exploded start, 3x the size of PR #170's view
                          (2700 x 2040), no balloons
    exploded_ids.png      8-bit map: pixel value = 1 + index of the instance
                          seen there (0 = background)
    exploded_parts.json   for each index: instance name, BOM item and number,
                          and its projected anchor (PR #170's balloon point)

The outputs are committed, so make_exploded_view.py runs without CAD tools.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "assets" / "exploded"
SCALE = 3                                   # PR #170 rendered the view at 900 x 680


def main(fa: Path) -> None:
    sys.path.insert(0, str(fa / "onshape"))
    sys.path.insert(0, str(fa))
    import vtk
    from PIL import Image
    from vtkmodules.util.numpy_support import vtk_to_numpy

    import assembly_bom as ab
    import build

    order, inst = ab.scene()
    rows = ab.bom(order)
    no_of = {r["item"]: r["no"] for r in rows}
    name_of = {r["item"]: r["name"] for r in rows}

    size = (900 * SCALE, 680 * SCALE)
    view = ab.View(order, inst, size)
    # the camera of assembly_exploded_bom.png (assembly_bom.main: cam_exploded)
    zero, one = (lambda k: 0.0), (lambda k: 1.0)
    view.camera(np.vstack([ab._points(order, inst, zero), ab._points(order, inst, one)]),
                margin=0.9)
    view.pose(zero)
    view.win.SetMultiSamples(8)
    OUT.mkdir(parents=True, exist_ok=True)
    view.image().save(OUT / "exploded_render.png", optimize=True)

    # part-ID map: flat, unlit, one colour per instance, no anti-aliasing
    view.win.SetMultiSamples(0)
    saved = {}
    for i, d in enumerate(order):
        a = view.actors[d["name"]]
        p = a.GetProperty()
        saved[d["name"]] = (p.GetColor(), p.GetAmbient(), p.GetDiffuse(), p.GetSpecular())
        p.SetColor((i + 1) / 255.0, 0.0, 0.0)
        p.SetAmbient(1.0), p.SetDiffuse(0.0), p.SetSpecular(0.0)
        p.LightingOff()
    view.ren.SetBackground(0, 0, 0)
    view.win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(view.win)
    w2i.ReadFrontBufferOff()
    w2i.Update()
    img = w2i.GetOutput()
    w, h, _ = img.GetDimensions()
    a = vtk_to_numpy(img.GetPointData().GetScalars()).reshape(h, w, -1)[::-1, :, :3]
    ids = np.ascontiguousarray(a[:, :, 0]).astype(np.uint8)
    Image.fromarray(ids, mode="L").save(OUT / "exploded_ids.png", optimize=True)

    parts = []
    for i, d in enumerate(order):
        pj = (build.W2J @ np.append(ab.anchor_world(d, inst, zero), 1.0))[:3]
        x, y = view.project(pj)
        parts.append(dict(id=i + 1, name=d["name"], item=d["item"], no=no_of[d["item"]],
                          item_name=name_of[d["item"]], anchor=[round(x, 1), round(y, 1)],
                          pixels=int((ids == i + 1).sum())))
    meta = dict(source="PR #170 pipeline, branch claude/issue-165-20261001-1931, commit 7f5b3b7, "
                       "cad/full-assembly/assembly_bom.py (scene, bom, View, camera of "
                       "assembly_exploded_bom.png)",
                size=list(size), scale=SCALE,
                bom=[dict(no=r["no"], name=r["name"], qty=r["qty"], kind=r["kind"]) for r in rows],
                parts=parts)
    (OUT / "exploded_parts.json").write_text(json.dumps(meta, indent=1) + "\n")
    print("wrote", OUT / "exploded_render.png", OUT / "exploded_ids.png",
          OUT / "exploded_parts.json", f"({len(parts)} instances, {len(rows)} BOM rows)")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/fa/cad/full-assembly").resolve())
