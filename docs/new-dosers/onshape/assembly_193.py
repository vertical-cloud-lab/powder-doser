"""Exploded, labelled diagram of the current doser: the #193 Onshape assembly.

    python assembly_193.py fetch    # 3 + 2 per part read-only Onshape calls; STLs go to $ASM_DIR (default /tmp/asm/data)
    xvfb-run -a python assembly_193.py render

`fetch` reads the assembly definition and BOM, then exports one STL per unique part
at the exact document version the assembly uses (Onshape redirects STL exports to
another host, so the redirect is followed with the same key). Every call is logged
in api_calls.jsonl. `render` places each part with its occurrence transform, turns
the model upright (the assembly is modelled with +Z pointing down), moves each part
out along the direction it goes on, and writes ../assembly/doser_193_exploded.png.
Fasteners aren't modelled in #193; the labels give the ones in inventory-checklist.csv.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assembly"
DATA = Path(os.environ.get("ASM_DIR", "/tmp/asm/data"))
DID, WID, EID = "f866631c78fbefd61e6856e4", "043fe020d0194e41cea13bc2", "3156bac055c13d8160e229b4"
FLIP = np.diag([1.0, -1.0, -1.0, 1.0])  # Onshape assembly: +Z is down. Rotate 180 deg about X.


def fetch() -> None:
    from client import Onshape
    DATA.joinpath("stl").mkdir(parents=True, exist_ok=True)
    o = Onshape(budget=3, run="pr181-assembly-diagram")
    json.dump(o.get(f"documents/d/{DID}/w/{WID}/elements"), open(DATA / "elements.json", "w"), indent=1)
    asm = o.get(f"assemblies/d/{DID}/w/{WID}/e/{EID}",
                params={"includeMateFeatures": "true", "includeMateConnectors": "true", "includeNonSolids": "false"})
    json.dump(asm, open(DATA / "assembly.json", "w"), indent=1)
    json.dump(o.get(f"assemblies/d/{DID}/w/{WID}/e/{EID}/bom", params={"indented": "false", "generateIfAbsent": "true"}),
              open(DATA / "bom.json", "w"), indent=1)
    uniq = {(i["documentId"], i["documentVersion"], i["elementId"], i["partId"]) for i in asm["rootAssembly"]["instances"]}
    o = Onshape(budget=2 * len(uniq) + 4, run="pr181-assembly-diagram")
    for did, vid, eid, pid in sorted(uniq):
        fn = DATA / "stl" / f"{did[:6]}_{eid[:6]}_{pid}.stl"
        if fn.exists():
            continue
        r = o.get(f"partstudios/d/{did}/v/{vid}/e/{eid}/stl", raw=True, allow_redirects=False, headers={"Accept": "*/*"},
                  params={"partIds": pid, "mode": "binary", "units": "millimeter", "grouping": "true",
                          "angleTolerance": 0.1, "chordTolerance": 0.02, "minFacetWidth": 0.05})
        if r.status_code in (301, 302, 303, 307, 308):
            r = o.get(r.headers["Location"], raw=True, headers={"Accept": "*/*"})
        fn.write_bytes(r.content)
    print("calls", o.calls)


# ---- what each part is, how it's drawn, and where it moves in the exploded view -----------------
# Offsets are (x, y, z) in mm in the upright frame: +y is the auger's outlet end (front), +z is up.
UP_PLATE = 70.0
GROUPS = [
    # key, label, sub-label, instance names, colour, offset per instance
    ("legs", "Wood legs ×3", "9.5 × 59 × 250 mm, 2 stand bolts each", ["Part 1 <5>", "Part 1 <6>", "Part 1 <7>"],
     "#c8a06a", {"Part 1 <5>": (60, 0, -45), "Part 1 <6>": (-60, 0, -45), "Part 1 <7>": (0, -60, -45)}),
    ("sides", "Stand brackets, sides ×2", "left + right; 2 stand bolts each into the base", ["Part 1 <3>", "Part 1 <2>"],
     "#7f8fa6", {"Part 1 <3>": (32, 0, -22), "Part 1 <2>": (-32, 0, -22)}),
    ("back", "Stand bracket, back", "2 stand bolts into the base (#193 mates 1)", ["Part 1 <1>"], "#5d6d7e", {"Part 1 <1>": (0, -32, -22)}),
    ("base", "Base", "190 × 190 mm, H2D print", ["Part 1 <4>"], "#aab7c4", {"Part 1 <4>": (0, 0, 0)}),
    ("servos", "MG996R servos ×2", "4 × M3×14 + locknut each", ["MG-996R <2>", "MG-996R <3>", "MG-996R <4>", "MG-996R <1>"],
     "#2c3e50", {"MG-996R <2>": (55, 0, 0), "MG-996R <3>": (55, 0, 0), "MG-996R <4>": (-55, 0, 0), "MG-996R <1>": (-55, 0, 0)}),
    ("spinions", "Servo pinions 14T ×2", "M3×10 into each servo shaft", ["Spur gear (14 teeth) <2>", "Spur gear (14 teeth) <1>"],
     "#e0a526", {"Spur gear (14 teeth) <2>": (28, 0, 0), "Spur gear (14 teeth) <1>": (-28, 0, 0)}),
    ("plate", "Mounting plate", "one piece with both 28T tilt gears;\nhinge: M5×40 + M5 locknut, each side", ["Part 1 <8>"],
     "#4f86c6", {"Part 1 <8>": (0, 0, UP_PLATE)}),
    ("stepper", "NEMA-11 stepper", "4 × M2.5×8 into the plate", ["stepper_motor <1>"], "#3d3d3d", {"stepper_motor <1>": (0, -55, UP_PLATE)}),
    ("ppinion", "Stepper pinion 20T", "on the stepper shaft; drives the auger's 44T gear", ["Stepper Pinion <1>"], "#d4ac0d",
     {"Stepper Pinion <1>": (35, 0, UP_PLATE + 10)}),
    ("tcbase", "Tap-collar base (hard stop)", "M3×25 + M3×30 flat head, 2 locknuts", ["tap_collar_base <1>"], "#8e5ea2",
     {"tap_collar_base <1>": (0, 0, UP_PLATE + 22)}),
    ("clips", "Flexible brackets (C-clips) ×2", "2 × M3×20 + locknut each", ["Part 1 <9>", "Part 1 <10>"], "#e67e22",
     {"Part 1 <9>": (0, 0, UP_PLATE + 50), "Part 1 <10>": (0, 0, UP_PLATE + 50)}),
    ("auger", "Auger", "44T gear; snaps into the C-clips", ["Part 1 <11>"], "#d9d9d9", {"Part 1 <11>": (0, 0, UP_PLATE + 115)}),
    ("cap", "Auger cap", "screws onto the auger's back end", ["auger_cap <1>"], "#c0392b", {"auger_cap <1>": (0, -55, UP_PLATE + 115)}),
    ("collar", "Tap collar", "slides onto the auger; clamp: M3×20 + locknut", ["Body1 <1>"], "#16a085",
     {"Body1 <1>": (0, 30, UP_PLATE + 160)}),
    ("solenoid", "Solenoid, 12 V push-pull", "2 × M3×5 into the tap collar", ["solenoid_coil <1>", "solenoid_plunger <1>", "solenoid_yoke <1>"],
     "#b87333", {"solenoid_coil <1>": (-35, 30, UP_PLATE + 200), "solenoid_plunger <1>": (-35, 30, UP_PLATE + 200),
                 "solenoid_yoke <1>": (-35, 30, UP_PLATE + 200)}),
]


def parts(explode: bool):
    import trimesh
    A = json.load(open(DATA / "assembly.json"))
    RA = A["rootAssembly"]
    inst = {i["id"]: i for i in RA["instances"]}
    group_of = {n: g for g in GROUPS for n in g[3]}
    out = []
    for occ in RA["occurrences"]:
        i = inst[occ["path"][-1]]
        T = np.array(occ["transform"], float).reshape(4, 4)
        T[:3, 3] *= 1000.0
        m = trimesh.load(DATA / "stl" / f"{i['documentId'][:6]}_{i['elementId'][:6]}_{i['partId']}.stl", force="mesh")
        m.apply_transform(FLIP @ T)
        g = group_of[i["name"]]
        if explode:
            m.apply_translation(g[5][i["name"]])
        out.append((g, i["name"], m))
    return out


def render_view(explode: bool, size, cam, zoom=1.0):
    import pyvista as pv
    P = parts(explode)
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background("white")
    for g, name, m in P:
        p.add_mesh(pv.wrap(m), color=g[4], smooth_shading=False, specular=0.15, ambient=0.18, diffuse=0.85)
    p.enable_parallel_projection()
    p.camera_position = cam
    p.reset_camera()
    p.camera.zoom(zoom)
    p.enable_anti_aliasing("ssaa")
    p.render()
    img = p.screenshot(return_img=True)
    depth = p.get_image_depth(fill_value=np.nan)
    # Screen anchor per instance: a visible vertex near the middle of the part's visible area.
    import vtk
    coord = vtk.vtkCoordinate()
    coord.SetCoordinateSystemToWorld()
    cam_pos = np.array(p.camera.position)
    H, W = img.shape[:2]
    anchors = {}
    for g, name, m in P:
        v = m.vertices[np.random.default_rng(0).choice(len(m.vertices), min(len(m.vertices), 2500), replace=False)]
        xy, vis = [], []
        for pt in v:
            coord.SetValue(*pt)
            dx, dy = coord.GetComputedDoubleDisplayValue(p.renderer)
            px, py = int(round(dx)), int(round(H - dy))
            if not (0 <= px < W and 0 <= py < H):
                continue
            dz = depth[py, px]
            dist = np.linalg.norm(pt - cam_pos)
            if np.isfinite(dz) and abs(abs(dz) - dist) < 6 + 0.02 * dist:
                xy.append((dx, H - dy))
        if xy:
            xy = np.array(xy)
            med = np.median(xy, 0)
            anchors[name] = xy[np.argmin(np.linalg.norm(xy - med, axis=1))]
    p.close()
    return img, anchors


def layout(ys, lo, hi, gap):
    """Spread label centres (sorted by ys) so that they're at least `gap` apart within [lo, hi]."""
    order = np.argsort(ys)
    pos = np.array(ys, float)[order]
    for k in range(1, len(pos)):
        pos[k] = max(pos[k], pos[k - 1] + gap)
    over = pos[-1] - hi if len(pos) else 0
    if over > 0:
        pos -= over
        for k in range(len(pos) - 2, -1, -1):
            pos[k] = min(pos[k], pos[k + 1] - gap)
    pos = np.maximum(pos, lo + np.arange(len(pos)) * gap)
    out = np.empty_like(pos)
    out[order] = pos
    return out


FASTENERS = """Fasteners per doser (inventory-checklist.csv)
M3×14 socket head ×8      M3×20 button head ×5
M3×10 socket head ×2      M3×25 button head ×1
M3×5 socket head ×2       M3×30 flat head ×1
M2.5×8 socket head ×4     M5×40 button head ×2
M3 nylon-insert locknut ×15
M5 nylon-insert locknut ×2
Stand bolt + nut, 7 mm holes ×12 (size not chosen)"""


def render() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    OUT.mkdir(exist_ok=True)
    R = 1800
    img, anc = render_view(True, (R, R), [(520, 700, 520), (-15, -40, 40), (0, 0, 1)], zoom=1.0)
    img_as, _ = render_view(False, (900, 900), [(430, 560, 330), (-15, -40, -60), (0, 0, 1)], zoom=1.15)

    FW, FH = 2600, 1700
    fig = plt.figure(figsize=(FW / 100, FH / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FW); ax.set_ylim(FH, 0); ax.axis("off")
    top = 120                      # title band
    side = FH - top - 10           # drawn size of the exploded render
    x0 = (FW - side) / 2 - 10
    ax.imshow(img, extent=[x0, x0 + side, top + side, top])
    k = side / R
    anc = {n: np.array([x0 + p[0] * k, top + p[1] * k]) for n, p in anc.items()}

    items = []
    for g in GROUPS:
        names = {"servos": ["MG-996R <2>", "MG-996R <4>"], "solenoid": ["solenoid_coil <1>"]}.get(g[0], g[3])
        pts = [anc[n] for n in names if n in anc]
        if pts:
            items.append([g, pts, np.mean(pts, 0)])
    cx = x0 + side / 2
    left = [it for it in items if it[2][0] < cx]
    right = [it for it in items if it[2][0] >= cx]
    inset = (20, top + 10, 520, 520)               # x, y, w, h of the assembled view
    box_h = 250                                    # fastener box at the bottom right
    cols = {"L": (left, x0 - 10, inset[1] + inset[3] + 40, FH - 40),
            "R": (right, x0 + side + 10, top + 30, FH - box_h - 60)}
    for sd, (its, xt, lo, hi) in cols.items():
        ys = layout([it[2][1] for it in its], lo, hi, 92)
        for (g, pts, c), y in zip(its, ys):
            # one leader, to the instance nearest this column
            pt = min(pts, key=lambda p: p[0]) if sd == "L" else max(pts, key=lambda p: p[0])
            ha = "right" if sd == "L" else "left"
            sw = -1 if sd == "L" else 1
            ax.text(xt + sw * 30, y - 4, g[1], ha=ha, va="bottom", fontsize=17, fontweight="bold", color="#1b1b1b")
            ax.text(xt + sw * 30, y + 2, g[2], ha=ha, va="top", fontsize=13, color="#4a4a4a", linespacing=1.15)
            ax.plot([xt + sw * 12], [y - 14], marker="s", ms=13, color=g[4], mec="#333333", mew=0.7)
            ax.plot([xt + sw * 4, pt[0]], [y - 14, pt[1]], color="#3a3a3a", lw=1.0)
            ax.plot([pt[0]], [pt[1]], marker="o", ms=6, color="#1b1b1b")
    ax.text(FW / 2, 18, "Powder doser: current assembly (#193), exploded", ha="center", va="top", fontsize=30, fontweight="bold")
    ax.text(FW / 2, 70, "Onshape Assembly f866631c, as of 7 Nov 2026. Fasteners aren't modelled in #193; the grey lines name the ones "
            "in inventory-checklist.csv. ×2 / ×3: one leader shown.", ha="center", va="top", fontsize=15, color="#444444")
    ax.imshow(img_as, extent=[inset[0], inset[0] + inset[2], inset[1] + inset[3], inset[1]])
    ax.text(inset[0] + 10, inset[1] + 10, "Assembled", fontsize=18, fontweight="bold", va="top")
    ax.text(FW - 30, FH - 30, FASTENERS, ha="right", va="bottom", multialignment="left", fontsize=14, family="DejaVu Sans Mono", linespacing=1.35,
            bbox=dict(boxstyle="round,pad=0.6", fc="#f4f6f8", ec="#9aa5b1"))
    fig.savefig(OUT / "doser_193_exploded.png", dpi=100, facecolor="white")
    print("wrote", OUT / "doser_193_exploded.png")


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    {"fetch": fetch, "render": render}[sys.argv[1]]()
