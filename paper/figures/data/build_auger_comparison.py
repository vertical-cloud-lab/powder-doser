#!/usr/bin/env python3
"""SI table: the AI-modelled geared auger against the auger used in the tests.

AI-modelled auger: the parametric OpenSCAD model that the coding agent wrote
in pull request #49 (branch copilot/add-new-auger-design, May 2026):
cad/auger-geared/auger-core.scad (geometry and parameters),
archimedes-auger-geared.scad (250 mm variant), gear-teeth.scad (tooth
profile) and stepper-pinion.scad (16-tooth pinion).  Its values are read from
those parameters.  The blade thickness along the axis, which the code does
not state, is worked out from them and checked on the committed STL.  The
same pull request's later threaded storage auger and cap (June 2026:
storage-auger-core.scad, nozzle-variants.scad,
threaded-storage-auger-core.scad) are parsed as well, for the CSV and the
table footnote.

Tested auger: the team's Fusion 360 parts that ran every test ("Threaded
Auger Final" and "Cap Final" STLs from the issue #117 zip, committed in
PR #170 under cad/full-assembly/components/fusion/) and the stepper pinion
STEP (components/fusion-step/stepper-pinion.step), measured here with
trimesh and checked against the dimensions that build_auger_section.py wrote
to assets/auger_section.json.  Lengths along the tube are measured from the
outlet (z = 0).

Writes auger_comparison.csv (every value, with the AI threaded storage
variant and the sources) and auger_comparison_table.tex (SI table,
label tbl:augercompare).

Usage:  python3 build_auger_comparison.py
Requires trimesh, shapely, networkx, numpy and cascadio (STEP import).
"""

from __future__ import annotations

import csv
import io
import json
import math
import pathlib
import re
import subprocess
import sys

import numpy as np
import trimesh
from shapely.geometry import LineString, Polygon

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_auger_section import BRANCH as FUSION_BRANCH  # noqa: E402
from build_auger_section import FUSION_DIR  # noqa: E402

AI_BRANCH = "origin/copilot/add-new-auger-design"      # pull request #49
AI_DIR = "cad/auger-geared"
STEP_DIR = "cad/full-assembly/components/fusion-step"
CSV_OUT = HERE / "auger_comparison.csv"
TEX_OUT = HERE / "auger_comparison_table.tex"


# ----------------------------------------------------------------------------
# sources
# ----------------------------------------------------------------------------
def _blob(branch: str, path: str) -> bytes:
    return subprocess.run(["git", "show", f"{branch}:{path}"], check=True,
                          capture_output=True, cwd=HERE).stdout


def _mesh(branch: str, path: str) -> trimesh.Trimesh:
    kind = path.rsplit(".", 1)[-1].lower()
    loaded = trimesh.load(io.BytesIO(_blob(branch, path)), file_type=kind)
    mesh = loaded.to_geometry() if hasattr(loaded, "to_geometry") else loaded
    if mesh.extents.max() < 1.0:                    # STEP comes in metres
        mesh.apply_scale(1000.0)
    return mesh


def _scad_params(*names: str) -> dict[str, float]:
    """Numeric `name = expression;` assignments from the AI's OpenSCAD files."""
    params: dict[str, float] = {"PI": math.pi}
    assign = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*([^;]+);", re.M)
    for name in names:
        text = _blob(AI_BRANCH, f"{AI_DIR}/{name}").decode()
        text = re.sub(r"//[^\n]*", "", text)
        for key, expr in assign.findall(text):
            try:
                params[key] = float(eval(" ".join(expr.split()),
                                         {"__builtins__": {}}, params))
            except Exception:                       # module-local expressions
                pass
    return params


def _module_defaults(name: str, module: str) -> dict[str, float]:
    """Default arguments of an OpenSCAD module, e.g. the cap's wall."""
    text = _blob(AI_BRANCH, f"{AI_DIR}/{name}").decode()
    sig = re.search(rf"module\s+{module}\s*\(([^)]*)\)", text).group(1)
    return {k: float(v) for k, v in re.findall(r"(\w+)\s*=\s*([\d.]+)", sig)}


# ----------------------------------------------------------------------------
# mesh sections
# ----------------------------------------------------------------------------
def _even_odd(loops) -> object:
    geom = None
    for loop in loops:
        if len(loop) < 4:
            continue
        poly = Polygon(loop).buffer(0)
        geom = poly if geom is None else geom.symmetric_difference(poly)
    return geom


def _polys(geom) -> list[Polygon]:
    parts = geom.geoms if hasattr(geom, "geoms") else [geom]
    return [p for p in parts if p.geom_type == "Polygon"]


def _hsec(mesh: trimesh.Trimesh, z: float):
    """Solid region of the plane normal to the axis at height z."""
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    return None if sec is None else _even_odd(l[:, :2] for l in sec.discrete)


def _asec(mesh: trimesh.Trimesh, phi_deg: float = 0.0):
    """Solid region of the half-plane through the axis at angle phi, in (r, z)."""
    phi = np.deg2rad(phi_deg)
    d = np.array([np.cos(phi), np.sin(phi), 0.0])
    n = np.array([-np.sin(phi), np.cos(phi), 0.0])
    sec = mesh.section(plane_origin=[0, 0, 0], plane_normal=n)
    return _even_odd(np.c_[l @ d, l[:, 2]] for l in sec.discrete)


def _crossings(geom, x: float, z0: float = -1.0, z1: float = 400.0):
    hit = geom.intersection(LineString([(x, z0), (x, z1)]))
    segs = hit.geoms if hasattr(hit, "geoms") else [hit]
    return sorted((min(c[1] for c in s.coords), max(c[1] for c in s.coords))
                  for s in segs if not s.is_empty)


def _radii(geom) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """Radii along the outer and inner boundaries of a section."""
    outer, inner = [], []
    for p in _polys(geom):
        outer.append(np.hypot(*np.asarray(p.exterior.coords).T))
        inner += [np.hypot(*np.asarray(i.coords).T) for i in p.interiors]
    return outer, inner


def _teeth(geom) -> tuple[int, float, float]:
    """Tooth count, tip and root radius of the outermost loop of a section."""
    p = max(_polys(geom), key=lambda q: q.exterior.length)
    x, y = np.asarray(p.exterior.coords).T
    r, th = np.hypot(x, y), np.arctan2(y, x)
    order = np.argsort(th)
    grid = np.linspace(-np.pi, np.pi, 7200, endpoint=False)
    rr = np.interp(grid, th[order], r[order], period=2 * np.pi)
    above = rr > 0.5 * (rr.max() + rr.min())
    return int(np.sum(above & ~np.roll(above, 1))), float(r.max()), float(r.min())


def _free_volume(mesh: trimesh.Trimesh, z_top: float, bore_r: float,
                 dz: float = 0.25) -> float:
    """Open volume inside the tube (mL), from sections every dz mm."""
    zs = np.arange(dz / 2, z_top, dz)
    area = np.full(len(zs), np.nan)
    for k, z in enumerate(zs):
        geom = _hsec(mesh, z)
        if geom is None:
            continue
        holes = [Polygon(i).area for p in _polys(geom) for i in p.interiors
                 if np.hypot(*np.asarray(i.coords).T).max() < bore_r + 0.3]
        if holes:
            area[k] = sum(holes)
    ok = ~np.isnan(area)                            # skip failed sections
    area = np.interp(zs, zs[ok], area[ok])
    return float(area.sum() * dz / 1000.0)


def _fit_cone(mesh: trimesh.Trimesh, zs) -> tuple[np.ndarray, np.ndarray]:
    """Linear fits r(z) of the outlet cone wall and of the core inside it."""
    rows = []
    for z in zs:
        _, inner = _radii(_hsec(mesh, z))
        ring = max(inner, key=len)
        rows.append((z, ring.min(), ring.max()))
    z, r_core, r_cone = np.asarray(rows).T
    return np.polyfit(z, r_core, 1), np.polyfit(z, r_cone, 1)


# ----------------------------------------------------------------------------
# measurements
# ----------------------------------------------------------------------------
def measure_tested() -> dict:
    aug = _mesh(FUSION_BRANCH, f"{FUSION_DIR}/threaded-auger-final.stl")
    cap = _mesh(FUSION_BRANCH, f"{FUSION_DIR}/cap-final.stl")
    pin = _mesh(FUSION_BRANCH, f"{STEP_DIR}/stepper-pinion.step")
    m: dict = {"length": float(aug.bounds[1][2] - aug.bounds[0][2])}

    outer, inner = _radii(_hsec(aug, 150.0))      # facet vertices lie on
    m["od"] = 2 * float(outer[0].max())             # the true circles
    m["bore"] = 2 * float(inner[0].max())
    m["wall"] = (m["od"] - m["bore"]) / 2

    # flight and core in the axial section (half-plane at 0 deg)
    sec0 = _asec(aug, 0.0)
    m["core_top"] = _crossings(sec0, 0.0)[0][1]
    _, inner = _radii(_hsec(aug, 50.0))
    m["core_d"] = 2 * float(max(inner, key=len).min())
    blades = {x: [(a, b) for a, b in _crossings(sec0, x) if b - a < 1.5 and a > 13]
              for x in (4.3, 7.25, 10.3)}
    starts = np.array([a for a, _ in blades[7.25]])
    m["pitch"] = float(np.median(np.diff(starts)))
    m["blade_axial"] = {x: float(np.median([b - a for a, b in v]))
                        for x, v in blades.items()}
    rise = _crossings(_asec(aug, 30.0), 7.25, starts[0] - 1, starts[0] + 4)[0][0]
    m["flight_hand"] = "right" if rise > starts[0] else "left"
    # flight top: first height above the core where the bore is fully open
    full = Polygon(_ring_xy(aug, 150.0)).area
    for z in np.arange(m["core_top"], m["core_top"] + 3, 0.02):
        if Polygon(_ring_xy(aug, z)).area > full - 0.5:
            m["flight_top"] = float(z)
            break
    m["flight_bottom"] = _crossings(sec0, 1.0)[0][0]
    m["turns"] = (m["flight_top"] - m["flight_bottom"]) / m["pitch"]

    # tapered outlet: cone wall and core tip, fitted over 1-10 mm
    core_fit, cone_fit = _fit_cone(aug, np.arange(1.0, 10.5, 0.5))
    m["exit_d"] = 2 * float(np.polyval(cone_fit, 0.0))
    m["cone_len"] = float((m["bore"] / 2 - cone_fit[1]) / cone_fit[0])
    m["core_tip_d"] = 2 * float(np.polyval(core_fit, 0.0))

    # gear band
    m["gear_teeth"], tip, root = _teeth(_hsec(aug, 83.3))
    m["gear_tip_d"], m["gear_root_d"] = 2 * tip, 2 * root
    m["gear_module"] = m["gear_tip_d"] / (m["gear_teeth"] + 2)
    zs = np.arange(70.0, 95.0, 0.05)
    on = [z for z in zs if max(map(np.max, _radii(_hsec(aug, z))[0])) > 20]
    m["gear_z"] = (round(float(min(on)), 1), round(float(max(on)), 1))

    # cap thread on the tube: crests, roots and pitch in the axial section
    outer, inner = _radii(_hsec(aug, 240.0))
    m["thread_crest_d"] = 2 * float(max(r.max() for r in outer))
    m["thread_root_d"] = 2 * float(min(r.min() for r in outer))
    m["wall_under_thread"] = (m["thread_root_d"] - m["bore"]) / 2
    crests = _crossings(sec0, m["thread_crest_d"] / 2 - 0.1, 200, 260)
    m["thread_pitch"] = float(np.median(np.diff([a for a, _ in crests])))
    m["thread_start"] = crests[0][0]
    m["thread_len"] = m["length"] - m["thread_start"]

    # screw-on cap (its closed end is at z = 0..2 in the part file)
    m["cap_od"] = float(2 * np.hypot(*cap.vertices[:, :2].T).max())
    m["cap_h"] = float(cap.extents[2])
    m["cap_end_wall"] = float(cap.bounds[1][2])
    outer, inner = _radii(_hsec(cap, -10.0))
    m["cap_thread_d"] = (2 * float(inner[0].min()), 2 * float(inner[0].max()))

    # stepper pinion
    m["pinion_teeth"], tip, _ = _teeth(_hsec(pin, 5.0))
    m["pinion_tip_d"] = 2 * tip
    m["pinion_module"] = m["pinion_tip_d"] / (m["pinion_teeth"] + 2)

    m["free_ml"] = _free_volume(aug, m["length"], m["bore"] / 2)
    m["plain_ml"] = math.pi * (m["bore"] / 2) ** 2 * (m["length"] - m["flight_top"]) / 1000
    return m


def _ring_xy(mesh: trimesh.Trimesh, z: float) -> np.ndarray:
    """Largest inner ring (the open bore) of the section at height z."""
    rings = [np.asarray(i.coords) for p in _polys(_hsec(mesh, z))
             for i in p.interiors]
    return max(rings, key=lambda c: Polygon(c).area)


def measure_ai() -> dict:
    p = _scad_params("gear-teeth.scad", "auger-core.scad",
                     "archimedes-auger-geared.scad", "stepper-pinion.scad")
    a: dict = {"p": p}
    a["length"] = p["total_height_full"]
    a["od"], a["wall"] = p["outer_diameter"], p["wall_thickness"]
    a["bore"] = p["outer_diameter"] - 2 * p["wall_thickness"]
    a["core_d"] = 2 * p["shaft_r"]
    a["core_bottom"] = p["shaft_bottom_z"]
    a["core_top"] = a["length"] - p["top_cap_height"]
    a["pitch"], a["blade_code"] = p["fin_pitch"], p["fin_thickness"]
    # linear_extrude(twist) of a rectangle fin_thickness wide: the blade is
    # that wide across a section normal to the axis, so along the axis it is
    # pitch * (angle it subtends) / 360 deg, thinner toward the wall
    a["blade_axial"] = {r: p["fin_pitch"] * 2 * math.asin(p["fin_thickness"] / 2 / r)
                        / (2 * math.pi) for r in (p["shaft_r"], 7.25, a["bore"] / 2)}
    a["flight_bottom"], a["flight_top"] = a["core_bottom"], a["core_top"]
    a["turns"] = (a["flight_top"] - a["flight_bottom"]) / a["pitch"]
    a["exit_d"], a["cone_len"] = p["exit_hole_d"], p["bottom_cap_h"]
    a["cone_top_d"] = 2 * (a["bore"] / 2 - 0.5)
    a["gear_teeth"], a["gear_module"] = int(p["gear_teeth"]), p["gear_module"]
    a["gear_tip_d"] = 2 * p["gear_tip_r"]
    a["gear_root_d"] = 2 * p["gear_root_r"]
    zc, w = p["gear_center_z_full"], p["gear_face_width"]
    a["gear_z"] = (round(zc - w / 2, 1), round(zc + w / 2, 1))
    a["pinion_teeth"] = int(p["pinion_teeth"])
    a["slots"] = (int(p["slot_count"]), p["slot_length"], p["slot_width"])
    a["top_wall"], a["m3_pilot_d"] = p["top_cap_height"], p["m3_pilot_d"]

    # check the blade thickness along the axis on the committed STL
    stl = _mesh(AI_BRANCH, f"{AI_DIR}/archimedes-auger-geared.stl")
    sec0 = _asec(stl, 0.0)
    a["blade_axial_stl"] = {x: float(np.median([b - c for c, b in _crossings(sec0, x)
                                                if b - c < 1.5 and c > 13]))
                            for x in (4.3, 7.25, 10.3)}
    starts = [c for c, b in _crossings(sec0, 7.25) if b - c < 1.5 and c > 13]
    rise = _crossings(_asec(stl, 30.0), 7.25, starts[0] - 1, starts[0] + 4)[0][0]
    a["flight_hand"] = "right" if rise > starts[0] else "left"
    a["free_ml"] = _free_volume(stl, a["core_top"], a["bore"] / 2)

    # the agent's later threaded storage variant (same pull request, June)
    s = _scad_params("gear-teeth.scad", "auger-core.scad", "nozzle-variants.scad",
                     "storage-auger-core.scad", "threaded-storage-auger-core.scad",
                     "threaded_archimedes-auger-storage.scad")
    cap = _module_defaults("threaded-storage-auger-core.scad", "threaded_storage_cap")
    r_in = s["thread_crest_r"] + s["thread_clear"]
    a["storage"] = {
        "screw_top": s["total_height_full"] * s["screw_fraction"],
        "tip_d": 2 * s["taper_tip_bottom_r"],
        "thread": (s["thread_len"], s["thread_pitch"], 2 * s["thread_crest_r"],
                   2 * s["thread_minor_r"]),
        "cap": (2 * (r_in + cap["cap_wall"]),
                s["thread_len"] + cap["cap_gap_above"] + cap["cap_top"]),
        "gear_teeth": int(s["gear_teeth"]),
    }
    return a


# ----------------------------------------------------------------------------
# table
# ----------------------------------------------------------------------------
def _n(x: float, nd: int = 1) -> str:
    """Number without a trailing .0."""
    s = f"{x:.{nd}f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def rows(a: dict, t: dict) -> list[dict]:
    """Table rows (LaTeX); 'storage' is the AI threaded storage variant (CSV)."""
    st = a["storage"]
    mm = "~mm"
    same = "Unchanged"
    mid = a["blade_axial"][7.25]
    return [
        dict(feature="Overall length", ai=f"{_n(a['length'])}{mm}",
             tested=f"{_n(t['length'])}{mm}", change=same),
        dict(feature="Outer diameter", ai=f"{_n(a['od'])}{mm}",
             tested=f"{_n(t['od'])}{mm}", change=same),
        dict(feature="Bore", ai=f"{_n(a['bore'])}{mm}",
             tested=f"{_n(t['bore'])}{mm}", change=same),
        dict(feature="Wall thickness", ai=f"{_n(a['wall'])}{mm}",
             tested=f"{_n(t['wall'])}{mm}; {_n(t['wall_under_thread'])}{mm} "
                    "under the cap thread",
             change="Thinner under the thread$^a$",
             storage=f"{_n(a['wall'])} mm; "
                     f"{_n(st['thread'][3] / 2 - a['bore'] / 2)} mm under the thread"),
        dict(feature="Core",
             ai=f"{_n(a['core_d'])}{mm} across, {_n(a['core_bottom'])}--"
                f"{_n(a['core_top'], 0)}{mm} from the outlet",
             tested=f"{_n(t['core_d'])}{mm} across, 0--{_n(t['core_top'], 0)}{mm}; "
                    f"tapers to {_n(t['core_tip_d'])}{mm} at the exit",
             change="Outlet third only; carried down to the exit$^a$",
             storage=f"8 mm across, 0-{_n(st['screw_top'])} mm; tapers to "
                     f"{_n(st['tip_d'])} mm at the exit"),
        dict(feature="Flight thickness",
             ai=f"{_n(a['blade_code'])}{mm} across the blade in the code; "
                f"{_n(a['blade_axial'][a['bore'] / 2])}--"
                f"{_n(a['blade_axial'][a['p']['shaft_r']])}{mm} along the axis, "
                "thinnest at the wall",
             tested=f"{_n(t['blade_axial'][7.25])}{mm} along the axis, the same "
                    "at every radius",
             change=f"Uniform; about the same at mid-radius ({_n(mid, 2)}{mm} "
                    "in the AI model)",
             storage="as the geared auger"),
        dict(feature="Flight pitch", ai=f"{_n(a['pitch'])}{mm}",
             tested=f"{_n(t['pitch'])}{mm}",
             change=f"{_n(100 * (t['pitch'] / a['pitch'] - 1), 0)}\\% longer",
             storage=f"{_n(a['pitch'])} mm"),
        dict(feature="Flighted length",
             ai=f"{_n(a['flight_bottom'])}--{_n(a['flight_top'], 0)}{mm} "
                f"({_n(a['turns'], 0)} turns)",
             tested=f"{_n(t['flight_bottom'], 0)}--{_n(t['flight_top'], 0)}{mm} "
                    f"({_n(t['turns'], 0)} turns)",
             change="Outlet third only$^a$",
             storage=f"0.5-{_n(st['screw_top'])} mm"),
        dict(feature="Number of starts",
             ai=f"One, {a['flight_hand']}-handed",
             tested=f"One, {t['flight_hand']}-handed", change=same),
        dict(feature="Outlet and exit hole",
             ai=f"{_n(a['cone_len'])}{mm} cone, {_n(a['cone_top_d'])} to "
                f"{_n(a['exit_d'])}{mm} across; the core stops where it meets "
                f"the cone, {_n(a['core_bottom'])}{mm} above the exit",
             tested=f"{_n(t['cone_len'])}{mm} cone, {_n(t['bore'])} to "
                    f"{_n(t['exit_d'])}{mm} across; flight and core reach the exit",
             change="Flight and core carried down to the exit$^a$",
             storage="12 mm cone, 20 to 3 mm across; tapered core and flight "
                     "reach the exit"),
        dict(feature="Gear",
             ai=f"{a['gear_teeth']} teeth, module {_n(a['gear_module'])}, "
                f"{_n(a['gear_tip_d'])}{mm} over the tips, "
                f"{_n(a['gear_z'][1] - a['gear_z'][0])}{mm} wide, "
                f"{_n(a['gear_z'][0], 0)}--{_n(a['gear_z'][1], 0)}{mm} "
                "from the outlet",
             tested=f"{t['gear_teeth']} teeth, module {_n(t['gear_module'])}, "
                    f"{_n(t['gear_tip_d'])}{mm} over the tips, "
                    f"{_n(t['gear_z'][1] - t['gear_z'][0])}{mm} wide, "
                    f"{_n(t['gear_z'][0], 0)}--{_n(t['gear_z'][1], 0)}{mm} "
                    "from the outlet",
             change=f"{WORDS[a['gear_teeth'] - t['gear_teeth']].capitalize()} fewer teeth; "
                    "same module, width, and position",
             storage=f"{st['gear_teeth']} teeth"),
        dict(feature="Drive pinion and reduction",
             ai=f"{a['pinion_teeth']} teeth; "
                f"{_n(a['gear_teeth'] / a['pinion_teeth'], 1)}:1",
             tested=f"{t['pinion_teeth']} teeth; "
                    f"{_n(t['gear_teeth'] / t['pinion_teeth'], 1)}:1",
             change="Lower reduction; same "
                    f"{_n((t['gear_teeth'] + t['pinion_teeth']) * t['pinion_module'] / 2, 0)}"
                    f"{mm} centre distance"),
        dict(feature="Filling",
             ai=f"{WORDS[a['slots'][0]].capitalize()} {_n(a['slots'][1])}~$\\times$~"
                f"{_n(a['slots'][2])}{mm} slots in the closed top end "
                f"({_n(a['top_wall'])}{mm} thick)",
             tested="Open top end under a screw-on cap",
             change="Cap replaces the slots$^a$",
             storage="open top end under a screw-on cap"),
        dict(feature="Reservoir",
             ai="No plain section; the flight fills the bore "
                f"({_n(a['free_ml'], 0)}~mL open volume)",
             tested=f"Plain bore above the flight ({_n(t['plain_ml'], 0)}~mL; "
                    f"{_n(t['free_ml'], 0)}~mL open volume in all)",
             change="Plain reservoir added$^a$",
             storage="plain bore above the flight"),
        dict(feature="Cap",
             ai="None; the closed top end has an M3 hole for a spindle",
             tested=f"Screw-on, {_n(t['cap_od'])}{mm} across and "
                    f"{_n(t['cap_h'])}{mm} long; thread of "
                    f"{_n(t['thread_pitch'])}{mm} pitch, "
                    f"{_n(t['thread_crest_d'])}{mm} over the crests, on the "
                    f"top {_n(t['thread_len'], 0)}{mm} of the tube",
             change="Cap added$^a$",
             storage=f"screw-on, {_n(st['cap'][0])} mm across and "
                     f"{_n(st['cap'][1])} mm long; thread of {_n(st['thread'][1])} mm "
                     f"pitch, {_n(st['thread'][2])} mm over the crests (flush "
                     f"with the tube), on the top {_n(st['thread'][0])} mm"),
        dict(feature="Modelled with",
             ai="OpenSCAD code written by an AI coding agent (May 2026)",
             tested="Fusion~360, by the team (July 2026)",
             change="Remodelled by hand in conventional CAD",
             storage="OpenSCAD code written by the AI coding agent (June 2026)"),
    ]


WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}


TEX_HEAD = r"""% Generated by paper/figures/data/build_auger_comparison.py -- do not edit by hand.
\begin{table}[htbp]
\centering
\small
\caption{The AI-modelled geared auger compared with the auger used in every
test. AI-modelled values are the parameters of the OpenSCAD model that the
coding agent wrote in May 2026 (\texttt{cad/auger-geared/auger-core.scad},
\texttt{archimedes-auger-geared.scad}, \texttt{gear-teeth.scad}, and
\texttt{stepper-pinion.scad}; pull request \#49). Tested values were measured
on the team's Fusion~360 files (\texttt{threaded-auger-final.stl},
\texttt{cap-final.stl}, and \texttt{stepper-pinion.step}; pull request \#170).
Lengths along the tube are measured from the outlet. Flight thickness is given
along the axis for both parts; the 2~mm in the AI code is the width of the
blade across a section normal to the axis. Values and their sources are in
\texttt{paper/figures/data/auger\_comparison.csv}.}
\label{tbl:augercompare}
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{2.3cm}>{\raggedright\arraybackslash}p{4.7cm}>{\raggedright\arraybackslash}p{4.7cm}>{\raggedright\arraybackslash}p{4.0cm}@{}}
\toprule
Feature & AI-modelled auger & Tested auger & What changed \\
\midrule
"""

TEX_TAIL = r"""\bottomrule
\end{tabular}
\par\smallskip
\parbox{16.5cm}{\footnotesize $^a$Already present in the agent's later
threaded storage auger and cap (\texttt{threaded-storage-auger-core.scad};
pull request \#49, June 2026), which it modelled at the team's request. The
team's Fusion~360 file of the tested auger is titled ``Auger Threaded
Storage''.}
\end{table}
"""


def _csv_text(s: str) -> str:
    """LaTeX markup to plain text for the CSV."""
    for a, b in (("~", " "), ("--", "-"), ("$\\times$", "x"),
                 ("$^a$", " (already in the AI threaded storage variant)"),
                 ("\\%", "%")):
        s = s.replace(a, b)
    return s


def _check_against_section(t: dict) -> None:
    """Warn if these measurements disagree with assets/auger_section.json."""
    path = HERE.parent / "assets" / "auger_section.json"
    if not path.exists():
        return
    d = json.loads(path.read_text())["dimensions"]
    pairs = [("length_mm", t["length"]), ("outer_diameter_mm", t["od"]),
             ("bore_mm", t["bore"]), ("core_diameter_mm", t["core_d"]),
             ("flight_pitch_mm", t["pitch"]),
             ("flight_axial_thickness_mm", t["blade_axial"][7.25]),
             ("gear_tip_diameter_mm", t["gear_tip_d"])]
    for key, value in pairs:
        if abs(d[key] - value) > 0.06:
            print(f"warning: {key} is {value:.2f} here, {d[key]} in auger_section.json")
    if abs(d["core_extent_mm"][1] - t["core_top"]) > 0.06:
        print("warning: core top differs from auger_section.json")


def main() -> None:
    ai = measure_ai()
    tested = measure_tested()
    _check_against_section(tested)
    table = rows(ai, tested)

    ai_src = (f"{AI_BRANCH} {AI_DIR}/: auger-core.scad, archimedes-auger-geared.scad, "
              "gear-teeth.scad, stepper-pinion.scad (parameters); "
              "archimedes-auger-geared.stl (blade thickness along the axis, hand, "
              "open volume)")
    st_src = (f"{AI_BRANCH} {AI_DIR}/: storage-auger-core.scad, nozzle-variants.scad, "
              "threaded-storage-auger-core.scad, threaded_archimedes-auger-storage.scad")
    t_src = (f"{FUSION_BRANCH} {FUSION_DIR}/threaded-auger-final.stl, cap-final.stl; "
             f"{STEP_DIR}/stepper-pinion.step (measured)")
    with CSV_OUT.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["feature", "ai_modelled_geared_auger", "tested_auger",
                    "what_changed", "ai_threaded_storage_variant",
                    "ai_source", "tested_source", "ai_storage_source"])
        for r in table:
            w.writerow([r["feature"], _csv_text(r["ai"]), _csv_text(r["tested"]),
                        _csv_text(r["change"]),
                        _csv_text(r.get("storage", "as the geared auger")),
                        ai_src, t_src, st_src])
    body = "".join(f"{r['feature']} & {r['ai']} & {r['tested']} & {r['change']} \\\\\n"
                   for r in table)
    TEX_OUT.write_text(TEX_HEAD + body + TEX_TAIL)

    print("AI blade along the axis (code):",
          {k: round(v, 3) for k, v in ai["blade_axial"].items()})
    print("AI blade along the axis (STL): ",
          {k: round(v, 3) for k, v in ai["blade_axial_stl"].items()})
    print("tested blade along the axis:   ",
          {k: round(v, 3) for k, v in tested["blade_axial"].items()})
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in tested.items()
           if k != "blade_axial"})
    print(f"wrote {CSV_OUT.name} and {TEX_OUT.name}")


if __name__ == "__main__":
    main()
