"""Hand-soldering animation of the FC-1 charge-amplifier board, from ../pcb/solder_steps.json.

Bare board with copper pads; for each step the part drops onto its pads, the iron visits each pad
and a solder fillet grows. Captions are the PCB worker's step captions (hand-soldering order).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import trimesh
from trimesh.creation import box as tbox, cylinder as tcyl, cone as tcone

from engine import FPS, Scene, Writer, ease, overlay
from assemblies import Comp, T

HERE = Path(__file__).resolve().parent
STEPS = HERE.parent / "pcb" / "solder_steps.json"


def _box(cx, cy, z0, w, l, h, rot):
    m = tbox(extents=[l, w, h])
    m.apply_translation([0, 0, z0 + h / 2])
    m.apply_transform(T(rz=rot))
    m.apply_translation([cx, cy, 0])
    return m


def build():
    d = json.loads(STEPS.read_text())
    t = d["board_thickness"]
    outline = np.array(d["board_outline"])[:, :2]
    from shapely.geometry import Polygon
    poly = Polygon(outline)
    for x, y, dia, _ in d["holes"]:
        from shapely.geometry import Point
        poly = poly.difference(Point(x, y).buffer(dia / 2, 24))
    board = trimesh.creation.extrude_polygon(poly, t)
    board.apply_translation([0, 0, -t])
    comps = [Comp("FC-1 bare board", board, "#1f7a3a", np.eye(4), 0, (0, 0, 0), "bought")]
    pads = []
    for s in d["steps"]:
        for (px, py, pw, ph) in s["pads"]:
            pads.append(_box(px, py, 0.0, ph, pw, 0.06, 0.0))
    comps.append(Comp("copper pads", trimesh.util.concatenate(pads), "#c9a227", np.eye(4), 0, (0, 0, 0), "bought"))
    if d.get("guard_area"):
        g = Polygon(np.array(d["guard_area"]))
        gm = trimesh.creation.extrude_polygon(g, 0.04)
        comps.append(Comp("guard ring (bare copper)", gm, "#d9b44a", np.eye(4), 0, (0, 0, 0), "bought", 0.9))
    parts = []
    for s in d["steps"]:
        body = _box(0, 0, 0.0, s["body_w"], s["body_l"], max(0.4, s["body_h"]), s["rot"])
        M = np.eye(4)
        M[:3, 3] = [s["x"], s["y"], 0.08]
        comps.append(Comp(s["ref"], body, s.get("colour", "#333333"), M, 1, (0, 0, 25), "bought"))
        parts.append(s)
    fillets = []
    for s in d["steps"]:
        fl = []
        for (px, py, pw, ph) in s["pads"]:
            r = max(0.25, min(pw, ph) * 0.55)
            m = trimesh.creation.icosphere(subdivisions=2, radius=r)
            m.apply_scale([1, 1, 0.55])
            M = np.eye(4)
            M[:3, 3] = [px, py, 0.1]
            fl.append((m, M))
        fillets.append(fl)
    return d, comps, parts, fillets


def iron_mesh():
    tip = tcone(radius=0.9, height=7.0, sections=24)
    tip.apply_transform(T(rx=180))
    tip.apply_translation([0, 0, 7.0])
    shaft = tcyl(radius=2.2, height=40, sections=24)
    shaft.apply_translation([0, 0, 7.0 + 20])
    grip = tcyl(radius=5.0, height=50, sections=24)
    grip.apply_translation([0, 0, 47 + 25])
    m = trimesh.util.concatenate([tip, shaft, grip])
    m.apply_transform(T(ry=-35))        # held at an angle
    return m


def solder_segment(w: Writer, max_s=75.0):
    d, comps, parts, fillets = build()
    sc = Scene(comps)
    n_fixed = 3 if len(comps) > 2 + len(parts) else 2
    part_idx = list(range(n_fixed, n_fixed + len(parts)))
    for i in part_idx:
        sc.show(i, False)
    # fillet actors (hidden until soldered)
    import pyvista as pv
    fil_actors = []
    for fl in fillets:
        acts = []
        for m, M in fl:
            a = sc.pl.add_mesh(pv.wrap(m), color="#dcdcdc", specular=0.9, specular_power=40, smooth_shading=True)
            a.user_matrix = M
            a.SetVisibility(False)
            acts.append(a)
        fil_actors.append(acts)
    iron = sc.pl.add_mesh(pv.wrap(iron_mesh()), color="#8d99a6", specular=0.6)
    iron.SetVisibility(False)
    title = "10. FC-1 charge amplifier: hand soldering (41 steps)"
    total_steps = len(parts)
    per_step = max(0.9, min(1.8, max_s / total_steps))
    drop_n = int(0.35 * FPS)
    f_glob = 0
    for k, s in enumerate(parts):
        i = part_idx[k]
        c = comps[i]
        sc.show(i, True)
        pads = fillets[k]
        n_solder = max(int(per_step * FPS) - drop_n, len(pads))
        for f in range(drop_n):
            u = ease((f + 1) / drop_n)
            M = c.M.copy(); M[2, 3] += 25 * (1 - u)
            sc.pose(i, M)
            sc.camera((25, 20, 0), -20 + 30 * f_glob / (total_steps * per_step * FPS), 52, 105)
            w.add(overlay(sc.grab(), title=title, caption=s["caption"][:92], step=f"{k + 1}/{total_steps}", tag="Soldering"))
            f_glob += 1
        sc.pose(i, c.M)
        iron.SetVisibility(True)
        for f in range(n_solder):
            j = min(len(pads) - 1, int(f / n_solder * len(pads)))
            px, py = pads[j][1][0, 3], pads[j][1][1, 3]
            M = np.eye(4); M[:3, 3] = [px, py, 0.3]
            iron.user_matrix = M
            fil_actors[k][j].SetVisibility(True)
            for jj in range(j):
                fil_actors[k][jj].SetVisibility(True)
            sc.camera((25, 20, 0), -20 + 30 * f_glob / (total_steps * per_step * FPS), 52, 105)
            w.add(overlay(sc.grab(), title=title, caption=s["caption"][:92], step=f"{k + 1}/{total_steps}", tag="Soldering"))
            f_glob += 1
        for a in fil_actors[k]:
            a.SetVisibility(True)
    iron.SetVisibility(False)
    for f in range(int(2.5 * FPS)):
        sc.camera((25, 20, 0), 10 + 60 * f / (2.5 * FPS), 40, 120)
        w.add(overlay(sc.grab(), title=title, caption="Done: wash the guard area with IPA, dry, then the bench test with a known charge",
                      tag="Soldering"))
    sc.close()


if __name__ == "__main__":
    import sys
    import time
    t0 = time.time()
    w = Writer(sys.argv[1])
    solder_segment(w)
    w.close()
    print("solder", w.n, "frames", round(time.time() - t0, 1), "s")
