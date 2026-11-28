"""Shared FEA plumbing for sim/fea: CAD geometry -> gmsh tet10 mesh -> CalculiX deck -> results.

Units everywhere in the decks: mm, N, MPa, tonne/mm^3, s (so frequencies come out in Hz).
All results are computed, not measured.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CAD = HERE.parents[1] / "cad"
GEOM = HERE / "geom"
RUNS = Path(os.environ.get("FEA_SCRATCH", "/tmp/fea-scratch"))

# PLA (task brief). E_LOW is a 3-wall / 25 % infill lower bound.
PLA = dict(E=3500.0, E_LOW=2300.0, nu=0.36, rho=1.24e-9, sy=50.0, sy_layer=25.0, s_fat=15.0)
STEEL = dict(E=193000.0, nu=0.29, rho=8.0e-9)      # 304 stainless
ALU = dict(E=69000.0, nu=0.33, rho=2.70e-9)
G = 9810.0  # mm/s^2


# ----------------------------------------------------------------------------------------------
# geometry: prefer the CAD worker's STEP export; else build from cad/parts.py; record which
# ----------------------------------------------------------------------------------------------
def sha12(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]


def get_step(name: str) -> tuple[Path, str]:
    """Return (step_path, provenance string) for a printed part."""
    out = CAD / "out" / "step" / f"{name}.step"
    if out.exists():
        return out, f"CAD export cad/out/step/{name}.step (sha256 {sha12(out)})"
    GEOM.mkdir(exist_ok=True)
    dst = GEOM / f"{name}.step"
    sys.path.insert(0, str(CAD))
    import importlib
    import cadquery as cq  # noqa: F401
    parts = importlib.import_module("parts")
    wp = parts.PARTS[name].fn()
    import cadquery as cq
    cq.exporters.export(wp, str(dst))
    return dst, f"built from cad/parts.py::{name} (parts.py sha256 {sha12(CAD / 'parts.py')}), STEP not yet exported"


# ----------------------------------------------------------------------------------------------
# mesh
# ----------------------------------------------------------------------------------------------
def mesh_tet10(build, lc_max, lc_min=None, refine=None, verbose=False):
    """build(gmsh) must create the OCC geometry, synchronize, and return a dict
    {name: (dim, [entity tags])} of physical groups to export as node sets.
    Volumes get one physical group per (dim=3) entry with the key starting with 'V'.
    Returns nodes (N,3), tets (M,10) in CalculiX order, vol_id per tet, nsets {name: node ids (1-based)},
    tri6 surfaces {name: (K,6) 1-based}."""
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1 if verbose else 0)
    gmsh.model.add("m")
    groups = build(gmsh)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", lc_max)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", lc_min or lc_max / 4)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 1)
    gmsh.option.setNumber("Mesh.MinimumElementsPerTwoPi", 12)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)  # straight-sided tet10: no inverted elements on small holes
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    if refine:
        refine(gmsh)
    pg = {}
    for name, (dim, tags) in groups.items():
        pg[name] = (dim, gmsh.model.addPhysicalGroup(dim, list(tags)))
    gmsh.model.mesh.generate(3)
    ntags, coords, _ = gmsh.model.mesh.getNodes()
    nodes = coords.reshape(-1, 3)
    order = np.argsort(ntags)
    ntags = ntags[order]
    nodes = nodes[order]
    remap = np.zeros(int(ntags.max()) + 1, dtype=np.int64)
    remap[ntags] = np.arange(1, len(ntags) + 1)
    tets, vid = [], []
    for name, (dim, tag) in pg.items():
        if dim != 3:
            continue
        for ent in gmsh.model.getEntitiesForPhysicalGroup(3, tag):
            et, etags, enodes = gmsh.model.mesh.getElements(3, ent)
            for t, en in zip(et, enodes):
                if t == 11:  # tet10
                    e = remap[np.asarray(en, dtype=np.int64)].reshape(-1, 10)
                    e = e[:, [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]]  # gmsh -> CalculiX edge order
                    tets.append(e)
                    vid.append(np.full(len(e), name))
    tets = np.vstack(tets)
    vid = np.concatenate(vid)
    nsets, surfs = {}, {}
    for name, (dim, tag) in pg.items():
        if dim == 3:
            continue
        nt, _ = gmsh.model.mesh.getNodesForPhysicalGroup(dim, tag)
        nsets[name] = np.unique(remap[np.asarray(nt, dtype=np.int64)])
        if dim == 2:
            tri = []
            for ent in gmsh.model.getEntitiesForPhysicalGroup(2, tag):
                et, _, en = gmsh.model.mesh.getElements(2, ent)
                for t, e in zip(et, en):
                    if t == 9:  # tri6
                        tri.append(remap[np.asarray(e, dtype=np.int64)].reshape(-1, 6))
            if tri:
                surfs[name] = np.vstack(tri)
    gmsh.finalize()
    # drop nodes not used by tets (e.g. embedded construction points)
    return nodes, tets, vid, nsets, surfs


def surface_entities_in_box(gmsh, xmin, ymin, zmin, xmax, ymax, zmax, eps=1e-3):
    ents = gmsh.model.getEntitiesInBoundingBox(xmin - eps, ymin - eps, zmin - eps,
                                               xmax + eps, ymax + eps, zmax + eps, 2)
    return [t for d, t in ents]


def pressure_cload(nodes, tri6, p, direction=None):
    """Consistent nodal forces of a uniform traction on 6-node triangles (flat): corner nodes 0,
    mid-side nodes 1/3 of the triangle's load each. direction=None -> along the triangle normal
    (sign as oriented by gmsh), else a fixed unit vector (traction p * direction per area).
    Returns {node_id: force vector}."""
    f = {}
    for t in tri6:
        a, b, c = nodes[t[0] - 1], nodes[t[1] - 1], nodes[t[2] - 1]
        n = np.cross(b - a, c - a)
        area = 0.5 * np.linalg.norm(n)
        d = n / np.linalg.norm(n) if direction is None else np.asarray(direction, float)
        for k in t[3:]:
            f[k] = f.get(k, 0.0) + p * area / 3.0 * d
    return f


def tri6_area(nodes, tri6):
    s = 0.0
    for t in tri6:
        a, b, c = nodes[t[0] - 1], nodes[t[1] - 1], nodes[t[2] - 1]
        s += 0.5 * np.linalg.norm(np.cross(b - a, c - a))
    return s


# ----------------------------------------------------------------------------------------------
# CalculiX deck
# ----------------------------------------------------------------------------------------------
def _ids(ids, per=12):
    ids = list(map(int, ids))
    return "\n".join(", ".join(map(str, ids[i:i + per])) for i in range(0, len(ids), per))


def write_inp(path, nodes, tets, vid, materials, nsets=None, extra_nodes=None, extra_model="", steps=""):
    """materials: {volume group name: dict(E, nu, rho)}. extra_nodes: {id: xyz} appended (springs)."""
    path = Path(path)
    with open(path, "w") as fh:
        fh.write("*HEADING\nsim/fea model (computed, not measured)\n*NODE, NSET=NALL\n")
        for i, (x, y, z) in enumerate(nodes, 1):
            fh.write(f"{i}, {x:.6f}, {y:.6f}, {z:.6f}\n")
        if extra_nodes:
            fh.write("*NODE, NSET=NEXTRA\n")
            for i, (x, y, z) in extra_nodes.items():
                fh.write(f"{i}, {x:.6f}, {y:.6f}, {z:.6f}\n")
        eid = 1
        for name in materials:
            sel = tets[vid == name]
            if len(sel) == 0:
                continue
            fh.write(f"*ELEMENT, TYPE=C3D10, ELSET=E{name}\n")
            for e in sel:
                fh.write(f"{eid}, " + ", ".join(map(str, e)) + "\n")
                eid += 1
        fh.write("*ELSET, ELSET=EALL\n" + ",\n".join(f"E{n}" for n in materials if (vid == n).any()) + "\n")
        for name, ids in (nsets or {}).items():
            fh.write(f"*NSET, NSET={name}\n{_ids(ids)}\n")
        for name, m in materials.items():
            if not (vid == name).any():
                continue
            # short fixed formats: CalculiX misreads long floats such as 8.060000000000001e-10
            fh.write(f"*MATERIAL, NAME=M{name}\n*ELASTIC\n{m['E']:.6g}, {m['nu']:.6g}\n*DENSITY\n{m['rho']:.6e}\n")
            fh.write(f"*SOLID SECTION, ELSET=E{name}, MATERIAL=M{name}\n")
        fh.write(extra_model)
        fh.write(steps)
    return path


def cload_block(fdict, scale=1.0):
    lines = ["*CLOAD"]
    for n, v in fdict.items():
        for k in range(3):
            if abs(v[k]) > 0:
                lines.append(f"{n}, {k + 1}, {scale * v[k]:.9e}")
    return "\n".join(lines) + "\n"


def run_ccx(inp: Path, timeout=1800):
    inp = Path(inp)
    env = dict(os.environ, OMP_NUM_THREADS="1", CCX_NPROC_EQUATION_SOLVER="1")
    r = subprocess.run(["ccx", "-i", inp.stem], cwd=inp.parent, env=env,
                       capture_output=True, text=True, timeout=timeout)
    if "Job finished" not in r.stdout:
        raise RuntimeError(f"ccx failed for {inp}:\n{r.stdout[-3000:]}\n{r.stderr[-2000:]}")
    return r.stdout


# ----------------------------------------------------------------------------------------------
# .dat parsing
# ----------------------------------------------------------------------------------------------
def parse_dat(path):
    """Return list of blocks: dict(kind, set, time, data) with data an (n, k) array (first column id)."""
    blocks, cur = [], None
    for line in open(path):
        s = line.strip()
        m = re.match(r"^(displacements|stresses|forces|total force|eigenvalue|strains)", s)
        if m and "for set" in s:
            kind = s.split("(")[0].strip()
            sname = re.search(r"for set (\S+)", s).group(1)
            t = re.search(r"time\s+([-\d.Ee+]+)", s)
            cur = dict(kind=kind, set=sname, time=float(t.group(1)) if t else None, rows=[])
            blocks.append(cur)
            continue
        if cur is not None:
            if not s:
                if cur["rows"]:
                    cur = None
                continue
            try:
                vals = [float(v) for v in s.split()]
                cur["rows"].append(vals)
            except ValueError:
                cur = None
    for b in blocks:
        b["data"] = np.array(b.pop("rows")) if b.get("rows") else np.zeros((0, 1))
    return blocks


def parse_freqs(path):
    txt = open(path).read()
    m = re.search(r"E I G E N V A L U E   O U T P U T(.*?)(P A R T I C I P|\Z)", txt, re.S)
    out = []
    if not m:
        return out
    for line in m.group(1).splitlines():
        v = line.split()
        if len(v) == 5:
            try:
                out.append(float(v[3]))  # cycles/time
            except ValueError:
                pass
    return out


def von_mises(s):
    sxx, syy, szz, sxy, sxz, syz = s.T
    return np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2)
                   + 3 * (sxy ** 2 + sxz ** 2 + syz ** 2))


def principal_max(s):
    out = np.empty(len(s))
    for i, (sxx, syy, szz, sxy, sxz, syz) in enumerate(s):
        out[i] = np.linalg.eigvalsh(np.array([[sxx, sxy, sxz], [sxy, syy, syz], [sxz, syz, szz]]))[-1]
    return out


def save_json(path, obj):
    def conv(o):
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
        return str(o)
    Path(path).write_text(json.dumps(obj, indent=2, default=conv))


# plotting style (dataviz skill palette, light mode)
PAL = ["#257de0", "#f47230", "#00b894", "#f2a600", "#ee7fac", "#008a17", "#6a4ce2", "#ec4647"]
INK, INK2 = "#191919", "#666666"


def style(ax, title=None, xlabel=None, ylabel=None):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelcolor=INK)
    ax.grid(True, color="#e6e6e6", lw=0.8)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, color=INK, fontsize=10, loc="left")
    if xlabel:
        ax.set_xlabel(xlabel, color=INK)
    if ylabel:
        ax.set_ylabel(ylabel, color=INK)
