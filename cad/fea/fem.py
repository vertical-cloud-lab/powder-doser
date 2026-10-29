"""Small CalculiX toolkit: gmsh meshes from the CAD's STEP parts, CalculiX decks, results, pictures.

Units throughout: mm, N, MPa, tonne (1 t = 1000 kg), s. Gravity is 9810 mm/s^2 and a density of
2.70e-9 t/mm^3 is 2700 kg/m^3.

    m = mesh_parts([Part("plate", step_path, M, "AL6061")], size=4)   # second-order tets (C3D10)
    d = Deck(m)                                                        # materials come from materials.py
    d.fix(m.nodes_where(lambda p: p[:, 2] < 1e-6))
    d.gravity()
    r = d.solve("work/plate")                                          # runs ccx, reads .frd/.dat
    r.umax, r.vm_max(), r.freqs ...

Parts that touch are fused by gmsh's fragment, so their meshes share nodes on the contact faces: a bonded
joint (the usual first assumption for a clamped bolted joint). Loads go on nodes, on element faces as pressure,
or through a rigid patch (a CalculiX *RIGID BODY) on a ring of nodes, for bolts and pins.
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import materials as MAT

G = 9810.0                                     # mm/s^2
CCX = shutil.which("ccx") or "ccx"
HERE = Path(__file__).resolve().parent
CAD = HERE.parent
WORK = Path(os.environ.get("FEA_WORK", "/tmp/fea-work"))

# gmsh's 10-node tet -> CalculiX C3D10 (= Abaqus = VTK): the last two mid-edge nodes swap
TET10_PERM = [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]
# C3D10 faces by corner node (0-based) and their CalculiX face labels
TET_FACES = {1: (0, 1, 2), 2: (0, 3, 1), 3: (1, 3, 2), 4: (2, 3, 0)}


# ----------------------------------------------------------------------------------------------- geometry input
@dataclass
class Part:
    name: str
    src: object                                # path to a STEP/BREP, or a callable(gmsh) -> list of volume tags
    M: np.ndarray | None = None                # 4x4 placement (world <- part)
    material: str = "AL6061"
    orient: tuple | None = None                # (a, b): local x along a, local y in the a-b plane (orthotropic parts)


def exported(design: str) -> Path:
    """Where export_design.py puts a design built from source (v3 and v4: their builds are not committed)."""
    return WORK / "designs" / design


def step_path(design: str, key: str) -> Path:
    """A component STEP: export_design.py's copy if there is one, else the design's own build
    (cad/<design>/step/components/<key>.step) or its reference/ folder."""
    for p in (exported(design) / "components" / f"{key}.step", CAD / design / "step" / "components" / f"{key}.step",
              CAD / design / "reference" / key):
        if p.exists():
            return p
    raise FileNotFoundError(f"{design}/{key}")


def placements(design: str) -> list[dict]:
    p = exported(design) / "placements.json"
    return json.loads((p if p.exists() else CAD / design / "placements.json").read_text())


def placement(design: str, name: str) -> np.ndarray:
    for p in placements(design):
        if p["name"] == name:
            return np.array(p["M"], float)
    raise KeyError(name)


# ----------------------------------------------------------------------------------------------- mesh
@dataclass
class Mesh:
    xyz: np.ndarray                            # (N, 3) node coordinates; CalculiX node id = index + 1
    tet: np.ndarray                            # (E, 10) node indices, C3D10 order; element id = index + 1
    part: np.ndarray                           # (E,) index into names
    names: list
    materials: list
    orients: list
    surf: dict = field(default_factory=dict)   # gmsh surface tag -> (K, 6) node indices of its 6-node triangles
    surf_part: dict = field(default_factory=dict)  # surface tag -> set of part indices it bounds
    h: float = 0.0
    _face_index: dict | None = None

    @property
    def n(self) -> int:
        return len(self.xyz)

    def elems_of(self, name: str) -> np.ndarray:
        return np.where(self.part == self.names.index(name))[0]

    def nodes_of(self, name: str) -> np.ndarray:
        return np.unique(self.tet[self.elems_of(name)])

    def corner_nodes(self) -> np.ndarray:
        return np.unique(self.tet[:, :4])

    def nodes_where(self, pred, part: str | None = None) -> np.ndarray:
        idx = self.nodes_of(part) if part else np.arange(self.n)
        return idx[pred(self.xyz[idx])]

    def faces(self, parts: list | None = None) -> list:
        """Every boundary/interface triangle as (tet index, face label, (6,) nodes) restricted to some parts."""
        if self._face_index is None:
            fi = {}
            for e, t in enumerate(self.tet):
                for lab, (a, b, c) in TET_FACES.items():
                    fi.setdefault(tuple(sorted((t[a], t[b], t[c]))), []).append((e, lab))
            self._face_index = fi
        keep = None if parts is None else {self.names.index(p) for p in parts}
        out = []
        for tag, tris in self.surf.items():
            for tri in tris:
                for e, lab in self._face_index.get(tuple(sorted(tri[:3])), []):
                    if keep is None or self.part[e] in keep:
                        out.append((e, lab, tri))
        return out

    def faces_where(self, pred, parts: list | None = None) -> list:
        """Faces whose centroid passes pred(centroid (3,), normal (3,)) -> bool; normal points out of the element."""
        out = []
        for e, lab, tri in self.faces(parts):
            p = self.xyz[tri[:3]]
            c = p.mean(0)
            n = np.cross(p[1] - p[0], p[2] - p[0])
            nn = np.linalg.norm(n)
            if nn == 0:
                continue
            n /= nn
            inside = self.xyz[self.tet[e, :4]].mean(0)
            if np.dot(n, c - inside) < 0:
                n = -n
            if pred(c, n):
                out.append((e, lab, tri, c, n, 0.5 * nn))
        return out

    def mass(self, rho_of=None) -> float:
        v = self.volumes()
        return float(sum(v[self.part == i].sum() * MAT.get(m).rho for i, m in enumerate(self.materials)))

    def volumes(self) -> np.ndarray:
        p = self.xyz[self.tet[:, :4]]
        return np.abs(np.einsum("ij,ij->i", p[:, 1] - p[:, 0], np.cross(p[:, 2] - p[:, 0], p[:, 3] - p[:, 0]))) / 6.0


def mesh_parts(parts: list[Part], size: float, size_min: float | None = None, curv: int = 10,
               refine: list | None = None, fuse: bool = True, threads: int = 4, verbose: bool = False,
               box_refine: list | None = None) -> Mesh:
    """Second-order tet mesh of the parts, fused (bonded) where they touch.

    refine: [(point (3,), radius, h)]: element size h within radius of the point, growing to size over 3 radii.
    box_refine: [((x0, y0, z0), (x1, y1, z1), h)].
    """
    import gmsh
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 1 if verbose else 0)
        gmsh.option.setNumber("General.NumThreads", threads)
        gmsh.model.add("m")
        owner = []                                         # per input volume: part index
        vols = []
        for ip, p in enumerate(parts):
            if callable(p.src):
                tags = [(3, t) for t in p.src(gmsh)]
            else:
                tags = [dt for dt in gmsh.model.occ.importShapes(str(p.src)) if dt[0] == 3]
            if p.M is not None:
                M = np.asarray(p.M, float)
                gmsh.model.occ.affineTransform(tags, list(M[:3, :].ravel()))
            vols += tags
            owner += [ip] * len(tags)
        gmsh.model.occ.synchronize()
        vol_part = {}
        if fuse and len(vols) > 1:
            _, omap = gmsh.model.occ.fragment(vols[:1], vols[1:])
            gmsh.model.occ.synchronize()
            for i, children in enumerate(omap):
                for dt in children:
                    if dt[0] == 3 and dt[1] not in vol_part:
                        vol_part[dt[1]] = owner[i]
            gmsh.model.occ.removeAllDuplicates()
            gmsh.model.occ.synchronize()
        else:
            for (d, t), o in zip(vols, owner):
                vol_part[t] = o
        gmsh.option.setNumber("Mesh.MeshSizeMax", size)
        gmsh.option.setNumber("Mesh.MeshSizeMin", size_min if size_min else size / 6)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", curv)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 1)
        gmsh.option.setNumber("Mesh.Algorithm", 6)
        gmsh.option.setNumber("Mesh.Algorithm3D", 10)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.option.setNumber("Mesh.SecondOrderLinear", 0)
        gmsh.option.setNumber("Mesh.Optimize", 1)
        fields = []
        for (pt, r, h) in (refine or []):
            f = gmsh.model.mesh.field.add("Ball")
            gmsh.model.mesh.field.setNumber(f, "Radius", r)
            gmsh.model.mesh.field.setNumber(f, "Thickness", 3 * r)
            gmsh.model.mesh.field.setNumber(f, "VIn", h)
            gmsh.model.mesh.field.setNumber(f, "VOut", size)
            for k, c in zip("XYZ", pt):
                gmsh.model.mesh.field.setNumber(f, k + "Center", float(c))
            fields.append(f)
        for (a, b, h) in (box_refine or []):
            f = gmsh.model.mesh.field.add("Box")
            gmsh.model.mesh.field.setNumber(f, "VIn", h)
            gmsh.model.mesh.field.setNumber(f, "VOut", size)
            for k, v0, v1 in zip("XYZ", a, b):
                gmsh.model.mesh.field.setNumber(f, k + "Min", float(v0))
                gmsh.model.mesh.field.setNumber(f, k + "Max", float(v1))
            gmsh.model.mesh.field.setNumber(f, "Thickness", 2 * size)
            fields.append(f)
        if fields:
            fm = gmsh.model.mesh.field.add("Min")
            gmsh.model.mesh.field.setNumbers(fm, "FieldsList", fields)
            gmsh.model.mesh.field.setAsBackgroundMesh(fm)
        gmsh.model.mesh.generate(3)
        nt, nc, _ = gmsh.model.mesh.getNodes()
        xyz_all = nc.reshape(-1, 3)
        gidx = np.full(int(nt.max()) + 1, -1, np.int64)
        gidx[nt.astype(np.int64)] = np.arange(len(nt))
        tets, tpart = [], []
        for (d, t) in gmsh.model.getEntities(3):
            if t not in vol_part:
                continue
            et, _, en = gmsh.model.mesh.getElements(3, t)
            for typ, conn in zip(et, en):
                if typ != 11:
                    continue
                c = gidx[np.asarray(conn, np.int64)].reshape(-1, 10)[:, TET10_PERM]
                tets.append(c)
                tpart.append(np.full(len(c), vol_part[t]))
        tet = np.vstack(tets)
        tp = np.concatenate(tpart)
        surf, surf_part = {}, {}
        for (d, s) in gmsh.model.getEntities(2):
            et, _, en = gmsh.model.mesh.getElements(2, s)
            for typ, conn in zip(et, en):
                if typ == 9:
                    surf[s] = gidx[np.asarray(conn, np.int64)].reshape(-1, 6)
            up, _ = gmsh.model.getAdjacencies(2, s)
            surf_part[s] = {vol_part[v] for v in up if v in vol_part}
    finally:
        gmsh.finalize()
    used = np.unique(tet)
    remap = np.full(len(xyz_all), -1, np.int64)
    remap[used] = np.arange(len(used))
    surf = {k: remap[v] for k, v in surf.items() if (remap[v] >= 0).all()}
    xyz = xyz_all[used].copy()
    tet = remap[tet]
    nfix = straighten_bad(xyz, tet)
    m = Mesh(xyz, tet, tp, [p.name for p in parts], [p.material for p in parts], [p.orient for p in parts],
             surf, surf_part, size)
    m.straightened = nfix
    return m


def _tet10_dets(xyz: np.ndarray, tet: np.ndarray) -> np.ndarray:
    """Jacobian determinants of each C3D10 at its 4 corners and its 4 integration points: (E, 8)."""
    a, b = 0.1381966011250105, 0.5854101966249685
    pts = [(1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1),
           (b, a, a, a), (a, b, a, a), (a, a, b, a), (a, a, a, b)]
    dL = np.array([[-1, -1, -1], [1, 0, 0], [0, 1, 0], [0, 0, 1]], float)
    edges = [(0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)]
    X = xyz[tet]                                             # (E, 10, 3)
    out = np.zeros((len(tet), len(pts)))
    for k, L in enumerate(pts):
        dN = np.zeros((10, 3))
        for i in range(4):
            dN[i] = (4 * L[i] - 1) * dL[i]
        for e, (i, j) in enumerate(edges):
            dN[4 + e] = 4 * (L[j] * dL[i] + L[i] * dL[j])
        J = np.einsum("eni,nj->eij", X, dN)                  # dx_i / dxi_j
        out[:, k] = np.linalg.det(J)
    return out


def straighten_bad(xyz: np.ndarray, tet: np.ndarray) -> int:
    """gmsh curves second-order nodes onto the CAD surfaces; on thin curved features that sometimes folds an
    element (CalculiX stops: 'nonpositive jacobian'). Put the mid-side nodes of every such element back on its
    straight edges (always valid when the linear tet is) and repeat until none is left. Returns the count."""
    edges = [(0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)]
    total = 0
    for _ in range(5):
        d = _tet10_dets(xyz, tet)
        lin = np.abs(d[:, :4]).mean(1)
        bad = np.where((d <= 1e-3 * lin[:, None]).any(1))[0]
        if len(bad) == 0:
            break
        total += len(bad)
        for e in bad:
            t = tet[e]
            for k, (i, j) in enumerate(edges):
                xyz[t[4 + k]] = 0.5 * (xyz[t[i]] + xyz[t[j]])
    return total


# ----------------------------------------------------------------------------------------------- deck
class Deck:
    """One CalculiX analysis on a Mesh: boundary conditions, loads and one step (static, frequency or buckle)."""

    def __init__(self, mesh: Mesh, materials: dict | None = None):
        self.m = mesh
        self.mat_override = materials or {}
        self.nsets: dict[str, np.ndarray] = {}
        self.bc: list = []                      # (nset, dof0, dof1, value)
        self.cloads: list = []                  # (node id, dof, value)
        self.dloads: list = []                  # (elem id, face label, pressure)
        self.grav: tuple | None = None
        self.rigid: list = []                   # (nset name, ref node id, rot node id)
        self.extra_nodes: list = []             # (id, xyz)
        self.springs: list = []                 # (node id, dof, k) grounded springs
        self.step = ("static", {})
        self.print_sets: list = []
        self.next_node = mesh.n + 1

    # sets ----------------------------------------------------------------------------------------
    def nset(self, name: str, idx) -> str:
        """Node set from 0-based mesh node indices (stored as CalculiX ids)."""
        idx = np.unique(np.asarray(idx, np.int64))
        if len(idx) == 0:
            raise ValueError(f"empty node set {name}")
        self.nsets[name] = idx + 1
        return name

    def nset_ids(self, name: str, ids) -> str:
        """Node set from CalculiX node ids (extra nodes: rigid-patch ref/rot nodes)."""
        self.nsets[name] = np.unique(np.asarray(ids, np.int64))
        return name

    def fix_ids(self, ids, dofs=(1, 2, 3), name: str | None = None, value: float = 0.0):
        name = name or f"FIXI{len(self.bc)}"
        self.nset_ids(name, ids)
        for d in dofs:
            self.bc.append((name, d, d, value))
        return name

    def node(self, xyz) -> int:
        nid = self.next_node
        self.next_node += 1
        self.extra_nodes.append((nid, np.asarray(xyz, float)))
        return nid

    # boundary conditions ----------------------------------------------------------------------------
    def fix(self, idx, dofs=(1, 2, 3), name: str | None = None, value: float = 0.0):
        name = name or f"FIX{len(self.bc)}"
        self.nset(name, idx)
        for d in dofs:
            self.bc.append((name, d, d, value))
        return name

    def spring(self, nid: int, dof: int, k: float):
        self.springs.append((nid, dof, k))

    def rigid_patch(self, idx, name: str, at=None) -> tuple[int, int]:
        """Tie the nodes into a rigid body; returns (ref node, rot node) to load or fix. ref at `at` (default centroid)."""
        self.nset(name, idx)
        c = self.m.xyz[np.asarray(idx)].mean(0) if at is None else np.asarray(at, float)
        r = self.node(c)
        q = self.node(c)
        self.rigid.append((name, r, q))
        return r, q

    # loads -------------------------------------------------------------------------------------------
    def gravity(self, direction=(0, 0, -1), g: float = G, factor: float = 1.0):
        d = np.asarray(direction, float)
        d /= np.linalg.norm(d)
        self.grav = (g * factor, d)

    def force(self, idx, F):
        """Total force F (3,) spread equally over the nodes (only for nodes on a rigid patch or a single node)."""
        idx = np.atleast_1d(np.asarray(idx))
        F = np.asarray(F, float) / len(idx)
        for i in idx:
            for d in range(3):
                if F[d] != 0:
                    self.cloads.append((int(i) + 1, d + 1, F[d]))

    def node_load(self, nid: int, F=None, M=None, rot: int | None = None):
        """Force on a (ref) node id; moment on its rot node."""
        if F is not None:
            for d in range(3):
                if F[d] != 0:
                    self.cloads.append((nid, d + 1, float(F[d])))
        if M is not None:
            for d in range(3):
                if M[d] != 0:
                    self.cloads.append((rot, d + 1, float(M[d])))

    def pressure(self, faces, p: float):
        for f in faces:
            self.dloads.append((f[0] + 1, f[1], p))

    def traction(self, faces, F):
        """Total force F (3,) as a uniform traction on the faces: pressure for the normal part and per-face
        equivalent surface loads; applied as consistent nodal loads of the 6-node triangles."""
        F = np.asarray(F, float)
        A = sum(f[5] for f in faces)
        t = F / A
        self._consistent(faces, lambda c, n: t)

    def bearing(self, faces, F, axis_pt, axis_dir):
        """Pin-in-hole bearing load: total F (3,) on the hole faces as a cosine pressure over the half facing F."""
        F = np.asarray(F, float)
        Fm = np.linalg.norm(F)
        d = F / Fm
        a = np.asarray(axis_dir, float)
        a /= np.linalg.norm(a)
        d = d - np.dot(d, a) * a
        d /= np.linalg.norm(d)
        sel, s = [], 0.0
        for f in faces:
            n = f[4] - np.dot(f[4], a) * a
            nn = np.linalg.norm(n)
            if nn < 0.3:
                continue
            c = -np.dot(n / nn, d)                 # outward normal of the hole points away from the load side
            if c > 0:
                sel.append((f, c))
                s += c * c * f[5] * nn
        p0 = Fm / s
        for f, c in sel:
            self.dloads.append((f[0] + 1, f[1], p0 * c))
        return p0

    def _consistent(self, faces, tfun):
        """Consistent nodal loads of a traction t(c, n) on 6-node triangles: corners 0, mid-sides A/3 each."""
        acc = {}
        for f in faces:
            tri, c, n, A = f[2], f[3], f[4], f[5]
            t = tfun(c, n)
            for k in tri[3:]:
                acc[k] = acc.get(k, 0) + t * A / 3.0
        for k, v in acc.items():
            for d in range(3):
                if v[d] != 0:
                    self.cloads.append((int(k) + 1, d + 1, float(v[d])))

    # steps -------------------------------------------------------------------------------------------
    def static(self, nlgeom: bool = False):
        self.step = ("static", {"nlgeom": nlgeom})

    def frequency(self, n: int = 10):
        self.step = ("frequency", {"n": n})

    def buckle(self, n: int = 3):
        self.step = ("buckle", {"n": n})

    def print_reactions(self, name: str):
        self.print_sets.append(name)

    # write / run -------------------------------------------------------------------------------------
    def write(self, path: Path):
        m = self.m
        L = []
        w = L.append
        w("*HEADING\nwritten by cad/fea/fem.py")
        w("*NODE, NSET=NALL")
        for i, p in enumerate(m.xyz):
            w(f"{i + 1}, {p[0]:.6f}, {p[1]:.6f}, {p[2]:.6f}")
        for nid, p in self.extra_nodes:
            w(f"{nid}, {p[0]:.6f}, {p[1]:.6f}, {p[2]:.6f}")
        for ip, name in enumerate(m.names):
            idx = np.where(m.part == ip)[0]
            if len(idx) == 0:
                continue
            w(f"*ELEMENT, TYPE=C3D10, ELSET=P{ip}")
            for e in idx:
                w(f"{e + 1}, " + ", ".join(str(int(v) + 1) for v in m.tet[e]))
        w("*ELSET, ELSET=EALL")
        names = [f"P{ip}" for ip in range(len(m.names)) if (m.part == ip).any()]
        for i in range(0, len(names), 8):
            w(", ".join(names[i:i + 8]))
        eid = len(m.tet) + 1
        if self.springs:
            for k, (nid, dof, kk) in enumerate(self.springs):
                w(f"*ELEMENT, TYPE=SPRING1, ELSET=SPR{k}\n{eid}, {nid}")
                w(f"*SPRING, ELSET=SPR{k}\n{dof}\n{kk}")
                eid += 1
        for name, idx in self.nsets.items():
            w(f"*NSET, NSET={name}")
            ids = [str(int(i)) for i in idx]
            for i in range(0, len(ids), 12):
                w(", ".join(ids[i:i + 12]))
        used = {}
        for ip, mname in enumerate(m.materials):
            if (m.part == ip).any():
                used.setdefault(self.mat_override.get(m.names[ip], mname), []).append(ip)
        for ip, name in enumerate(m.names):
            o = m.orients[ip]
            if o is not None and (m.part == ip).any():
                a, b = np.asarray(o[0], float), np.asarray(o[1], float)
                w(f"*ORIENTATION, NAME=OR{ip}, SYSTEM=RECTANGULAR\n{a[0]}, {a[1]}, {a[2]}, {b[0]}, {b[1]}, {b[2]}")
        for mname, ips in used.items():
            mt = MAT.get(mname)
            w(f"*MATERIAL, NAME={mt.key}")
            if mt.ortho:
                o = mt.ortho
                w("*ELASTIC, TYPE=ENGINEERING CONSTANTS")
                w(f"{o['E1']}, {o['E2']}, {o['E3']}, {o['nu12']}, {o['nu13']}, {o['nu23']}, {o['G12']}, {o['G13']},\n{o['G23']}, 0.")
            else:
                w(f"*ELASTIC\n{mt.E}, {mt.nu}")
            w(f"*DENSITY\n{mt.rho:.4e}")
            for ip in ips:
                ori = f", ORIENTATION=OR{ip}" if (m.orients[ip] is not None) else ""
                w(f"*SOLID SECTION, ELSET=P{ip}, MATERIAL={mt.key}{ori}")
        for name, r, q in self.rigid:
            w(f"*RIGID BODY, NSET={name}, REF NODE={r}, ROT NODE={q}")
            w(f"*NSET, NSET=R_{name}\n{r}, {q}")
        if self.bc and self.step[0] in ("frequency", "buckle"):
            w("*BOUNDARY")
            for name, d0, d1, v in self.bc:
                w(f"{name}, {d0}, {d1}")
        kind, opt = self.step
        if kind == "static":
            w("*STEP" + (", NLGEOM" if opt.get("nlgeom") else "") + "\n*STATIC")
            if self.bc:
                w("*BOUNDARY")
                for name, d0, d1, v in self.bc:
                    w(f"{name}, {d0}, {d1}, {v}")
        elif kind == "frequency":
            w(f"*STEP\n*FREQUENCY, STORAGE=NO\n{opt['n']}")
        elif kind == "buckle":
            w(f"*STEP\n*BUCKLE\n{opt['n']}, 1e-5, {max(4 * opt['n'], 24)}, 2000")
        if self.cloads:
            w("*CLOAD")
            for nid, d, v in self.cloads:
                w(f"{nid}, {d}, {v:.6e}")
        if self.dloads:
            w("*DLOAD")
            for e, lab, p in self.dloads:
                w(f"{e}, P{lab}, {p:.6e}")
        if self.grav is not None and kind != "frequency":
            g, d = self.grav
            w(f"*DLOAD\nEALL, GRAV, {g}, {d[0]:.6f}, {d[1]:.6f}, {d[2]:.6f}")
        w("*NODE FILE\nU")
        if kind == "static":
            w("*EL FILE\nS")
        for s in self.print_sets:
            w(f"*NODE PRINT, NSET={s}, TOTALS=ONLY\nRF")
        if kind == "static":
            for name, r, q in self.rigid:
                w(f"*NODE PRINT, NSET=R_{name}\nU, RF")
        w("*END STEP")
        path.write_text("\n".join(L) + "\n")

    def solve(self, job: str, threads: int = 1, keep: bool = False) -> "Result":
        """Run ccx single-threaded: this CalculiX 2.21 build returns wrong *BUCKLE factors with 4 OpenMP threads
        (0.98 N for an 805 N Euler load; right with 1 or 2), so nothing here trusts its threading. Cases run in
        parallel processes instead, at most CCX_SLOTS ccx at once machine-wide, each under a CCX_MEM_GB address-space
        cap: an over-big model then fails on its own instead of exhausting the runner's memory."""
        d = WORK / job
        d.mkdir(parents=True, exist_ok=True)
        inp = d / "job.inp"
        self.write(inp)
        env = dict(os.environ, OMP_NUM_THREADS=str(threads), CCX_NPROC_EQUATION_SOLVER=str(threads))
        t0 = time.time()
        with _slot():
            p = subprocess.run([CCX, "-i", "job"], cwd=d, env=env, capture_output=True, text=True, preexec_fn=_mem_cap)
        wall = time.time() - t0
        import resource
        self.maxrss_mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024.0
        (d / "ccx.log").write_text(p.stdout + p.stderr + f"\nwall {wall:.1f} s, peak child RSS so far {self.maxrss_mb:.0f} MB\n")
        if p.returncode != 0 or "*ERROR" in p.stdout:
            err = [l for l in p.stdout.splitlines() if "ERROR" in l][:5]
            raise RuntimeError(f"ccx failed in {d}: {err or p.stdout[-800:]}")
        r = Result(self, d, wall)
        if not keep:
            for f in ("job.inp",):
                pass
        return r


def _mem_cap():
    import resource
    gb = float(os.environ.get("CCX_MEM_GB", "4.5"))
    resource.setrlimit(resource.RLIMIT_AS, (int(gb * 2 ** 30), int(gb * 2 ** 30)))


class _slot:
    """One of CCX_SLOTS machine-wide ccx slots (flock on /tmp/fea-slots/<i>), waited for in turn."""

    def __enter__(self):
        import fcntl
        n = int(os.environ.get("CCX_SLOTS", "3"))
        d = Path("/tmp/fea-slots")
        d.mkdir(exist_ok=True)
        while True:
            for i in range(n):
                f = open(d / str(i), "w")
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.f = f
                    return self
                except OSError:
                    f.close()
            time.sleep(0.5)

    def __exit__(self, *a):
        self.f.close()


# ----------------------------------------------------------------------------------------------- results
def read_frd(path: Path) -> list[dict]:
    """Nodal result blocks of an ASCII .frd: [{name, step, value, data: {node id: values}}]."""
    blocks, cur, step_val = [], None, 0.0
    with open(path) as f:
        for line in f:
            if line.startswith("  100C"):
                try:
                    step_val = float(line[12:24])
                except ValueError:
                    step_val = 0.0
                cur = {"value": step_val, "ids": [], "vals": []}
            elif line.startswith(" -4") and cur is not None:
                cur["name"] = line[5:13].strip()
                cur["ncomp"] = int(line[13:18])
            elif line.startswith(" -1") and cur is not None and "name" in cur:
                cur["ids"].append(int(line[3:13]))
                s = line[13:].rstrip("\n")
                cur["vals"].append([float(s[i:i + 12]) for i in range(0, len(s) - 11, 12)])
            elif line.startswith(" -2") and cur is not None and "name" in cur:
                s = line[13:].rstrip("\n")
                cur["vals"][-1] += [float(s[i:i + 12]) for i in range(0, len(s) - 11, 12)]
            elif line.startswith(" -3") and cur is not None and "name" in cur:
                n = cur.get("ncomp", 0)
                vals = np.array([v[:n] if n else v for v in cur["vals"]], float)
                blocks.append({"name": cur["name"], "value": cur["value"], "ids": np.array(cur["ids"]), "vals": vals})
                cur = None
    return blocks


def von_mises(S: np.ndarray) -> np.ndarray:
    sx, sy, sz, txy, tyz, tzx = S.T
    return np.sqrt(0.5 * ((sx - sy) ** 2 + (sy - sz) ** 2 + (sz - sx) ** 2) + 3 * (txy ** 2 + tyz ** 2 + tzx ** 2))


def principal(S: np.ndarray) -> np.ndarray:
    T = np.zeros((len(S), 3, 3))
    T[:, 0, 0], T[:, 1, 1], T[:, 2, 2] = S[:, 0], S[:, 1], S[:, 2]
    T[:, 0, 1] = T[:, 1, 0] = S[:, 3]
    T[:, 1, 2] = T[:, 2, 1] = S[:, 4]
    T[:, 2, 0] = T[:, 0, 2] = S[:, 5]
    return np.linalg.eigvalsh(T)               # ascending: (min, mid, max)


class Result:
    def __init__(self, deck: Deck, d: Path, wall: float):
        self.deck, self.dir, self.wall = deck, d, wall
        m = deck.m
        blocks = read_frd(d / "job.frd") if (d / "job.frd").exists() else []
        n = m.n
        self.U = np.zeros((n, 3))
        self.S = np.zeros((n, 6))
        self.modes, self.freqs = [], []
        for b in blocks:
            ok = b["ids"] <= n
            ids = b["ids"][ok] - 1
            if b["name"] == "DISP":
                arr = np.zeros((n, 3))
                arr[ids] = b["vals"][ok][:, :3]
                if deck.step[0] == "static":
                    self.U = arr
                else:
                    self.modes.append(arr)
            elif b["name"] == "STRESS":
                self.S[ids] = b["vals"][ok][:, :6]
        self.dat = (d / "job.dat").read_text() if (d / "job.dat").exists() else ""
        if deck.step[0] == "frequency":
            self.freqs = _eigen(self.dat)
        if deck.step[0] == "buckle":
            self.factors = _buckle(self.dat)
        self.vm = von_mises(self.S)

    # summaries -------------------------------------------------------------------------------------
    def umag(self) -> np.ndarray:
        return np.linalg.norm(self.U, axis=1)

    def umax(self, part: str | None = None) -> float:
        idx = self.deck.m.nodes_of(part) if part else np.arange(self.deck.m.n)
        return float(self.umag()[idx].max())

    def vm_max(self, part: str | None = None, exclude: np.ndarray | None = None, exclude_r: float = 0.0) -> tuple:
        """Peak von Mises on a part's nodes, and where; nodes within exclude_r of `exclude` nodes are skipped
        (point-like supports and load patches give singular peaks)."""
        m = self.deck.m
        idx = m.nodes_of(part) if part else np.arange(m.n)
        if exclude is not None and len(exclude) and exclude_r > 0:
            from scipy.spatial import cKDTree
            d, _ = cKDTree(m.xyz[np.asarray(exclude)]).query(m.xyz[idx])
            idx = idx[d > exclude_r]
        k = idx[np.argmax(self.vm[idx])]
        return float(self.vm[k]), m.xyz[k].tolist()

    def reactions(self, name: str) -> np.ndarray:
        """Total reaction force of a node set printed with print_reactions()."""
        txt = self.dat
        i = txt.find(f"total force (fx,fy,fz) for set {name.upper()}")
        if i < 0:
            return np.zeros(3)
        line = txt[i:].splitlines()[2]
        return np.array([float(v) for v in line.split()[:3]])

    def rigid_disp(self, name: str) -> np.ndarray:
        """(u, rot) of a rigid patch's ref and rot nodes (from the .dat)."""
        r, q = [(a, b) for (n, a, b) in self.deck.rigid if n == name][0]
        txt = self.dat
        i = txt.find(f"displacements (vx,vy,vz) for set R_{name.upper()}")
        out = {}
        for line in txt[i:].splitlines()[2:6]:
            parts = line.split()
            if len(parts) >= 4 and parts[0].isdigit():
                out[int(parts[0])] = np.array([float(v) for v in parts[1:4]])
        return np.concatenate([out.get(r, np.zeros(3)), out.get(q, np.zeros(3))])


def _eigen(dat: str) -> list:
    i = dat.find("E I G E N V A L U E   O U T P U T")
    out = []
    if i < 0:
        return out
    for line in dat[i:].splitlines()[5:]:
        p = line.split()
        if len(p) >= 5 and p[0].isdigit():
            out.append(float(p[3]))
        elif out:
            break
    return out


def _buckle(dat: str) -> list:
    i = dat.find("B U C K L I N G   F A C T O R   O U T P U T")
    out = []
    if i < 0:
        return out
    for line in dat[i:].splitlines()[4:]:
        p = line.split()
        if len(p) == 2 and p[0].isdigit():
            out.append(float(p[1]))
        elif out:
            break
    return out


# ----------------------------------------------------------------------------------------------- pictures
def grid(m: Mesh, U: np.ndarray | None = None, scale: float = 0.0):
    import pyvista as pv
    cells = np.hstack([np.full((len(m.tet), 1), 10), m.tet]).ravel()
    types = np.full(len(m.tet), 24, np.uint8)               # VTK_QUADRATIC_TETRA
    pts = m.xyz + (scale * U if U is not None else 0)
    return pv.UnstructuredGrid(cells, types, pts)


def render(res: Result, png: Path, field: str = "vm", title: str = "", view=(1, -1, 0.8), up=(0, 0, 1),
           scale: float | None = None, clim=None, parts_ghost: list | None = None, mode: int | None = None,
           size=(1400, 1000), units: str | None = None, zoom: float = 1.0, show_edges: bool = False, cmap: str | None = None):
    """Deformed shape coloured by von Mises (field="vm"), displacement ("u") or a mode shape (mode=i)."""
    import pyvista as pv
    m = res.deck.m
    U = res.modes[mode] if mode is not None else res.U
    umag = np.linalg.norm(U, axis=1)
    L = float(np.ptp(m.xyz, axis=0).max())
    if scale is None:
        scale = 0.06 * L / max(umag.max(), 1e-12)
    g0 = grid(m)
    g = grid(m, U, scale)
    if field == "vm":
        g["v"] = res.vm
        label = "von Mises (MPa)"
    else:
        g["v"] = umag * (1000.0 if units == "um" else 1.0)
        label = "displacement (µm)" if units == "um" else ("mode shape (relative)" if mode is not None else "displacement (mm)")
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("white")
    surf = g.extract_surface(nonlinear_subdivision=2)
    pl.add_mesh(g0.extract_surface().extract_feature_edges(35), color="#9aa0a6", line_width=1, opacity=0.6)
    pl.add_mesh(surf, scalars="v", cmap=cmap or ("turbo" if field == "vm" else "viridis"), clim=clim, show_edges=show_edges,
                smooth_shading=True, scalar_bar_args=dict(title=label, color="black", vertical=True, position_x=0.86,
                                                          position_y=0.2, height=0.6, width=0.05, fmt="%.3g",
                                                          title_font_size=16, label_font_size=14))
    pl.add_mesh(surf.extract_feature_edges(35), color="black", line_width=1)
    pl.camera_position = "iso"
    c = m.xyz.mean(0)
    v = np.asarray(view, float)
    pl.camera.focal_point = c
    pl.camera.position = c + v / np.linalg.norm(v) * L * 2.2
    pl.camera.up = up
    pl.reset_camera()
    pl.camera.zoom(zoom)
    txt = title + (f"\ndeformation x{scale:.3g}" if scale else "")
    pl.add_text(txt, position="upper_left", font_size=11, color="black")
    png.parent.mkdir(parents=True, exist_ok=True)
    pl.screenshot(str(png))
    pl.close()
    return scale
